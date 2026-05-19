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
from runtime.core.dialogue_reasoner_hybrid import (  # noqa: E402
    HYBRID_REASONER_ID,
    parse_hybrid_reasoning_packet,
    render_hybrid_reasoning_prompt,
    score_hybrid_reasoning_case,
    should_call_llm_reasoning,
)
from runtime.providers.dialogue_reasoner_llm_client import (  # noqa: E402
    DEFAULT_REASONER_TEMPERATURE,
    OpenAICompatibleReasonerConfig,
    call_openai_compatible_reasoner,
    missing_provider_config,
    redacted_provider_config,
)
from scripts.run_dialogue_reasoner_001_baseline import (  # noqa: E402
    CASES_PATH as GUARD_CASES_PATH,
    RESULT_PATH as DIALOGUE_001_RESULT_PATH,
    compare_expected,
    prior_turns_to_session_state,
)
from scripts.run_dialogue_reasoner_002_provider_evaluation import (  # noqa: E402
    DEFAULT_ENV_FILE,
    config_value,
    load_env_file,
    resolve_path,
)
from scripts.run_live_demo_001_agent_voice_call import DEFAULT_CASES_PATH, load_campaign  # noqa: E402


EXPERIMENT_ID = "DIALOGUE-REASONER-003"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "dialogue-reasoner-003-hybrid-gate.json"
OUTPUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
DEFAULT_DRY_RESULT = OUTPUT_DIR / "dry_run_result.json"
DEFAULT_DRY_REPORT = OUTPUT_DIR / "dry_run_report.md"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_campaign_for_cases(case_payload: dict[str, Any]) -> dict[str, Any]:
    return load_campaign(str(case_payload["default_campaign_id"]), DEFAULT_CASES_PATH)


def summarize_boolean_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "case_count": len(results),
        "passed_count": sum(1 for result in results if result.get("pass") is True),
        "failed_cases": [result["case_id"] for result in results if result.get("pass") is not True],
    }


def latency_summary(results: list[dict[str, Any]]) -> dict[str, float | None]:
    latencies = [float(result["latency_ms"]) for result in results if isinstance(result.get("latency_ms"), (int, float))]
    return {
        "min": min(latencies) if latencies else None,
        "median": statistics.median(latencies) if latencies else None,
        "max": max(latencies) if latencies else None,
    }


def run_guard_cases(campaign: dict[str, Any]) -> list[dict[str, Any]]:
    guard_payload = read_json(GUARD_CASES_PATH)
    results = []
    for case in guard_payload["cases"]:
        session_state = prior_turns_to_session_state(case.get("prior_turns") or [])
        reasoning = reason_about_turn(str(case["transcript"]), session_state, campaign, mode="baseline")
        mismatches = compare_expected(reasoning, case["expected"])
        results.append(
            {
                "case_id": case["case_id"],
                "pass": not mismatches,
                "mismatches": mismatches,
                "provider_call_allowed": False,
                "provider_call_made": False,
                "reasoning": reasoning,
            }
        )
    return results


def run_invocation_cases(cases: list[dict[str, Any]], campaign: dict[str, Any]) -> list[dict[str, Any]]:
    results = []
    for case in cases:
        session_state = prior_turns_to_session_state(case.get("prior_turns") or [])
        reasoning = reason_about_turn(str(case["transcript"]), session_state, campaign, mode="baseline")
        actual = should_call_llm_reasoning(reasoning)
        expected = case["expected_provider_call_allowed"]
        results.append(
            {
                "case_id": case["case_id"],
                "expected_provider_call_allowed": expected,
                "actual_provider_call_allowed": actual,
                "provider_call_made": False,
                "reasoning": reasoning,
                "pass": actual is expected,
                "mismatches": {} if actual is expected else {"provider_call_allowed": {"expected": expected, "actual": actual}},
            }
        )
    return results


def planned_reasoning_case(case: dict[str, Any], campaign: dict[str, Any]) -> dict[str, Any]:
    session_state = prior_turns_to_session_state(case.get("prior_turns") or [])
    context = build_reasoning_context(str(case["transcript"]), session_state, campaign)
    reasoning = reason_about_turn(str(case["transcript"]), session_state, campaign, mode="baseline")
    prompt = render_hybrid_reasoning_prompt(
        transcript=str(case["transcript"]),
        context=context,
        deterministic_reasoning=reasoning,
        case_goal=str(case.get("case_goal") or ""),
    )
    return {
        "case_id": case["case_id"],
        "transcript_length": len(str(case["transcript"])),
        "prior_turn_count": len(case.get("prior_turns") or []),
        "prompt_char_count": len(prompt),
        "provider_call_allowed": should_call_llm_reasoning(reasoning),
        "deterministic_reasoning": reasoning,
    }


def run_reasoning_case(
    case: dict[str, Any],
    campaign: dict[str, Any],
    config: OpenAICompatibleReasonerConfig,
) -> dict[str, Any]:
    session_state = prior_turns_to_session_state(case.get("prior_turns") or [])
    context = build_reasoning_context(str(case["transcript"]), session_state, campaign)
    deterministic_reasoning = reason_about_turn(str(case["transcript"]), session_state, campaign, mode="baseline")
    provider_call_allowed = should_call_llm_reasoning(deterministic_reasoning)
    result: dict[str, Any] = {
        "case_id": case["case_id"],
        "provider_call_allowed": provider_call_allowed,
        "provider_calls_made": False,
        "text_sent_to_provider": False,
        "api_key_value_logged": False,
        "deterministic_reasoning": deterministic_reasoning,
    }
    if not provider_call_allowed:
        result.update({"pass": False, "mismatches": {"provider_call_allowed": False}})
        return result
    prompt = render_hybrid_reasoning_prompt(
        transcript=str(case["transcript"]),
        context=context,
        deterministic_reasoning=deterministic_reasoning,
        case_goal=str(case.get("case_goal") or ""),
    )
    call = call_openai_compatible_reasoner(config, prompt)
    result.update(
        {
            "provider_calls_made": call.get("provider_calls_made") is True,
            "text_sent_to_provider": call.get("text_sent_to_provider") is True,
            "api_key_value_logged": call.get("api_key_value_logged") is True,
            "latency_ms": call.get("latency_ms"),
            "http_status": call.get("http_status"),
            "usage": call.get("usage") or {},
            "raw_response_stored": call.get("raw_response_stored") is True,
        }
    )
    if call.get("error"):
        result.update({"pass": False, "error": call["error"], "mismatches": {"provider_error": call["error"]}})
        return result
    try:
        reasoning_packet = parse_hybrid_reasoning_packet(str(call.get("content") or ""))
        scored = score_hybrid_reasoning_case(reasoning_packet, case)
        result.update(
            {
                "hybrid_reasoning": reasoning_packet,
                "pass": scored["pass"],
                "mismatches": scored["mismatches"],
            }
        )
    except Exception as exc:
        result.update({"pass": False, "error": str(exc), "mismatches": {"parse_or_schema_error": str(exc)}})
    return result


def baseline_reference() -> dict[str, Any]:
    if not DIALOGUE_001_RESULT_PATH.exists():
        return {"experiment_id": "DIALOGUE-REASONER-001", "available": False}
    payload = read_json(DIALOGUE_001_RESULT_PATH)
    return {
        "experiment_id": payload.get("experiment_id"),
        "available": True,
        "passed_count": payload.get("passed_count"),
        "case_count": payload.get("case_count"),
        "provider_calls_made": payload.get("provider_calls_made"),
        "opens_prod_102": payload.get("opens_prod_102"),
    }


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    case_payload = read_json(CASES_PATH)
    campaign = load_campaign_for_cases(case_payload)
    reasoning_cases = list(case_payload["reasoning_quality_cases"])
    if args.max_reasoning_cases and args.max_reasoning_cases > 0:
        reasoning_cases = reasoning_cases[: args.max_reasoning_cases]

    guard_results = run_guard_cases(campaign)
    invocation_results = run_invocation_cases(case_payload["invocation_gate_cases"], campaign)
    planned_reasoning = [planned_reasoning_case(case, campaign) for case in reasoning_cases]

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
    base = {
        "experiment_id": EXPERIMENT_ID,
        "hybrid_reasoner_id": HYBRID_REASONER_ID,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "case_source": str(CASES_PATH.relative_to(ROOT)).replace("\\", "/"),
        "guard_case_source": str(GUARD_CASES_PATH.relative_to(ROOT)).replace("\\", "/"),
        "case_count": len(guard_results) + len(invocation_results) + len(reasoning_cases),
        "full_case_count": 100,
        "max_reasoning_cases": args.max_reasoning_cases if args.max_reasoning_cases and args.max_reasoning_cases > 0 else None,
        "default_live_enabled": False,
        "live_demo_response_behavior_changed": False,
        "runtime_route_override_allowed": False,
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
        "planned_reasoning_cases": planned_reasoning,
    }
    if not args.live:
        return {
            **base,
            "mode": "dry-run",
            "blocked_reason": "dry-run-mode",
            "provider_calls_made": False,
            "text_sent_to_provider": False,
            "missing_config": missing,
            "reasoning_quality_results": [],
            "reasoning_quality_summary": {
                "planned_case_count": len(reasoning_cases),
                "provider_case_count": 0,
                "passed_count": None,
                "failed_cases": [],
                "acceptance_threshold": 36 if len(reasoning_cases) == 40 else None,
                "latency_ms": {"min": None, "median": None, "max": None},
            },
        }
    if not args.consent_confirmed:
        return {
            **base,
            "mode": "live-blocked",
            "blocked_reason": "missing-consent-confirmed",
            "provider_calls_made": False,
            "text_sent_to_provider": False,
            "missing_config": missing,
            "reasoning_quality_results": [],
            "reasoning_quality_summary": {
                "planned_case_count": len(reasoning_cases),
                "provider_case_count": 0,
                "passed_count": None,
                "failed_cases": [],
                "acceptance_threshold": 36 if len(reasoning_cases) == 40 else None,
                "latency_ms": {"min": None, "median": None, "max": None},
            },
        }
    if missing:
        return {
            **base,
            "mode": "live-blocked",
            "blocked_reason": "missing-provider-config",
            "provider_calls_made": False,
            "text_sent_to_provider": False,
            "missing_config": missing,
            "reasoning_quality_results": [],
            "reasoning_quality_summary": {
                "planned_case_count": len(reasoning_cases),
                "provider_case_count": 0,
                "passed_count": None,
                "failed_cases": [],
                "acceptance_threshold": 36 if len(reasoning_cases) == 40 else None,
                "latency_ms": {"min": None, "median": None, "max": None},
            },
        }

    reasoning_results = [run_reasoning_case(case, campaign, config) for case in reasoning_cases]
    reasoning_summary = summarize_boolean_results(reasoning_results)
    reasoning_summary.update(
        {
            "planned_case_count": len(reasoning_cases),
            "provider_case_count": sum(1 for result in reasoning_results if result.get("provider_calls_made") is True),
            "acceptance_threshold": 36 if len(reasoning_cases) == 40 else None,
            "latency_ms": latency_summary(reasoning_results),
        }
    )
    return {
        **base,
        "mode": "live",
        "blocked_reason": None,
        "provider_calls_made": any(result.get("provider_calls_made") is True for result in reasoning_results),
        "text_sent_to_provider": any(result.get("text_sent_to_provider") is True for result in reasoning_results),
        "missing_config": [],
        "reasoning_quality_results": reasoning_results,
        "reasoning_quality_summary": reasoning_summary,
    }


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# DIALOGUE-REASONER-003 Hybrid Gate Evaluation",
        "",
        f"- Mode: `{payload['mode']}`",
        f"- Blocked reason: `{payload['blocked_reason']}`",
        f"- Cases: `{payload['case_count']}`",
        f"- Guard batch: `{payload['guard_summary']['passed_count']}/{payload['guard_summary']['case_count']}`",
        f"- Invocation gate batch: `{payload['invocation_gate_summary']['passed_count']}/{payload['invocation_gate_summary']['case_count']}`",
        (
            f"- Reasoning quality batch: `{payload['reasoning_quality_summary']['passed_count']}/"
            f"{payload['reasoning_quality_summary']['planned_case_count']}`"
            if payload["mode"] == "live"
            else f"- Planned reasoning quality cases: `{payload['reasoning_quality_summary']['planned_case_count']}`"
        ),
        f"- Provider calls made: `{str(payload['provider_calls_made']).lower()}`",
        f"- Text sent to provider: `{str(payload['text_sent_to_provider']).lower()}`",
        f"- API key value logged: `{str(payload['api_key_value_logged']).lower()}`",
        f"- Runtime route override allowed: `{str(payload['runtime_route_override_allowed']).lower()}`",
        f"- Opens PROD-102: `{str(payload['opens_prod_102']).lower()}`",
        "",
        "## Boundary",
        "",
        "- Deterministic runtime owns dialogue act, buyer intent, topic, sales stage, response strategy, safety boundary, and call control.",
        "- The provider may only return reasoning enrichment fields for allowed cases.",
        "- Provider config comes from ignored local env, process env, or explicit non-secret flags.",
        "- Live mode requires `--live` and `--consent-confirmed`.",
        "",
    ]
    if payload["mode"] == "live":
        lines.extend(["## Live Reasoning Results", ""])
        for result in payload["reasoning_quality_results"]:
            status = "pass" if result.get("pass") else "fail"
            lines.append(f"- `{result['case_id']}`: `{status}`, latency `{result.get('latency_ms')}` ms")
    else:
        lines.extend(["## Planned Provider Reasoning Cases", ""])
        for result in payload["planned_reasoning_cases"]:
            lines.append(
                f"- `{result['case_id']}`: allowed `{str(result['provider_call_allowed']).lower()}`, "
                f"prompt chars `{result['prompt_char_count']}`"
            )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate hybrid deterministic guard + LLM reasoning boundary.")
    parser.add_argument("--live", action="store_true", help="Actually call the configured provider for reasoning-quality cases.")
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
                "reasoning_quality": payload["reasoning_quality_summary"],
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
