#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if str(ROOT := Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core.dialogue_reasoner import (  # noqa: E402
    DIALOGUE_REASONER_ID,
    build_reasoning_context,
    parse_json_object,
    reason_about_turn,
    render_strict_json_reasoner_prompt,
    validate_reasoning_packet,
)
from runtime.providers.dialogue_reasoner_llm_client import (  # noqa: E402
    DEFAULT_REASONER_TEMPERATURE,
    OpenAICompatibleReasonerConfig,
    call_openai_compatible_reasoner,
    missing_provider_config,
    redacted_provider_config,
)
from scripts.run_dialogue_reasoner_001_baseline import (  # noqa: E402
    CASES_PATH,
    RESULT_PATH as BASELINE_RESULT_PATH,
    compare_expected,
    prior_turns_to_session_state,
)
from scripts.run_live_demo_001_agent_voice_call import DEFAULT_CASES_PATH, load_campaign  # noqa: E402


EXPERIMENT_ID = "DIALOGUE-REASONER-002"
OUTPUT_DIR = ROOT / "research" / "experiments" / "generated" / EXPERIMENT_ID
DEFAULT_DRY_RESULT = OUTPUT_DIR / "dry_run_result.json"
DEFAULT_DRY_REPORT = OUTPUT_DIR / "dry_run_report.md"
DEFAULT_ENV_FILE = ROOT / "runtime" / "config" / "local" / "dialogue_reasoner.env"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def resolve_path(path_text: str | None, fallback: Path) -> Path:
    if not path_text:
        return fallback
    path = Path(path_text)
    return path if path.is_absolute() else ROOT / path


def load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def config_value(name: str, args_value: str | None, file_values: dict[str, str]) -> str | None:
    value = args_value or os.environ.get(name) or file_values.get(name)
    if value is None:
        return None
    value = value.strip()
    return value or None


def load_cases_and_campaign() -> tuple[dict[str, Any], dict[str, Any]]:
    payload = read_json(CASES_PATH)
    campaign = load_campaign(str(payload["default_campaign_id"]), DEFAULT_CASES_PATH)
    return payload, campaign


def baseline_reference() -> dict[str, Any]:
    if not BASELINE_RESULT_PATH.exists():
        return {
            "experiment_id": DIALOGUE_REASONER_ID,
            "available": False,
            "passed_count": None,
            "case_count": None,
        }
    baseline = read_json(BASELINE_RESULT_PATH)
    return {
        "experiment_id": baseline.get("experiment_id"),
        "available": True,
        "passed_count": baseline.get("passed_count"),
        "case_count": baseline.get("case_count"),
        "provider_calls_made": baseline.get("provider_calls_made"),
        "opens_prod_102": baseline.get("opens_prod_102"),
    }


def planned_case_records(cases: list[dict[str, Any]], campaign: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for case in cases:
        session_state = prior_turns_to_session_state(case.get("prior_turns") or [])
        context = build_reasoning_context(str(case["transcript"]), session_state, campaign)
        prompt = render_strict_json_reasoner_prompt(context)
        records.append(
            {
                "case_id": case["case_id"],
                "transcript_length": len(str(case["transcript"])),
                "prior_turn_count": len(case.get("prior_turns") or []),
                "prompt_char_count": len(prompt),
                "expected": case["expected"],
            }
        )
    return records


def run_live_case(
    case: dict[str, Any],
    campaign: dict[str, Any],
    config: OpenAICompatibleReasonerConfig,
) -> dict[str, Any]:
    session_state = prior_turns_to_session_state(case.get("prior_turns") or [])
    context = build_reasoning_context(str(case["transcript"]), session_state, campaign)
    prompt = render_strict_json_reasoner_prompt(context)
    call = call_openai_compatible_reasoner(config, prompt)
    result: dict[str, Any] = {
        "case_id": case["case_id"],
        "provider_calls_made": call.get("provider_calls_made") is True,
        "text_sent_to_provider": call.get("text_sent_to_provider") is True,
        "api_key_value_logged": call.get("api_key_value_logged") is True,
        "latency_ms": call.get("latency_ms"),
        "http_status": call.get("http_status"),
        "usage": call.get("usage") or {},
        "raw_response_stored": call.get("raw_response_stored") is True,
    }
    if call.get("error"):
        result.update({"pass": False, "error": call["error"], "mismatches": {"provider_error": call["error"]}})
        return result
    try:
        reasoning = validate_reasoning_packet(parse_json_object(str(call.get("content") or "")))
        mismatches = compare_expected(reasoning, case["expected"])
        result.update(
            {
                "reasoning": reasoning,
                "expected": case["expected"],
                "pass": not mismatches,
                "mismatches": mismatches,
            }
        )
    except Exception as exc:
        result.update({"pass": False, "error": str(exc), "mismatches": {"parse_or_schema_error": str(exc)}})
    return result


def result_summary(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    latencies = [float(case["latency_ms"]) for case in case_results if isinstance(case.get("latency_ms"), (int, float))]
    return {
        "case_count": len(case_results),
        "passed_count": sum(1 for case in case_results if case.get("pass") is True),
        "failed_cases": [case["case_id"] for case in case_results if case.get("pass") is not True],
        "latency_ms": {
            "min": min(latencies) if latencies else None,
            "median": statistics.median(latencies) if latencies else None,
            "max": max(latencies) if latencies else None,
        },
    }


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    case_payload, campaign = load_cases_and_campaign()
    selected_cases = list(case_payload["cases"])
    if args.max_cases and args.max_cases > 0:
        selected_cases = selected_cases[: args.max_cases]
    planned_records = planned_case_records(selected_cases, campaign)
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
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "case_source": str(CASES_PATH.relative_to(ROOT)).replace("\\", "/"),
        "case_count": len(selected_cases),
        "full_case_count": len(case_payload["cases"]),
        "max_cases": args.max_cases if args.max_cases and args.max_cases > 0 else None,
        "planned_provider_call_count": len(selected_cases),
        "default_live_enabled": False,
        "live_demo_response_behavior_changed": False,
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
        "planned_cases": planned_records,
    }
    if not args.live:
        return {
            **base,
            "mode": "dry-run",
            "blocked_reason": "dry-run-mode",
            "provider_calls_made": False,
            "text_sent_to_provider": False,
            "missing_config": missing,
            "llm_results": [],
        }
    if not args.consent_confirmed:
        return {
            **base,
            "mode": "live-blocked",
            "blocked_reason": "missing-consent-confirmed",
            "provider_calls_made": False,
            "text_sent_to_provider": False,
            "missing_config": missing,
            "llm_results": [],
        }
    if missing:
        return {
            **base,
            "mode": "live-blocked",
            "blocked_reason": "missing-provider-config",
            "provider_calls_made": False,
            "text_sent_to_provider": False,
            "missing_config": missing,
            "llm_results": [],
        }

    llm_results = [run_live_case(case, campaign, config) for case in selected_cases]
    summary = result_summary(llm_results)
    return {
        **base,
        "mode": "live",
        "blocked_reason": None,
        "provider_calls_made": any(case.get("provider_calls_made") is True for case in llm_results),
        "text_sent_to_provider": any(case.get("text_sent_to_provider") is True for case in llm_results),
        "missing_config": [],
        "llm_results": llm_results,
        **summary,
    }


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# DIALOGUE-REASONER-002 LLM Provider Evaluation",
        "",
        f"- Mode: `{payload['mode']}`",
        f"- Blocked reason: `{payload['blocked_reason']}`",
        f"- Cases: `{payload.get('passed_count', 0)}/{payload['case_count']}`" if payload["mode"] == "live" else f"- Planned cases: `{payload['case_count']}`",
        f"- Provider calls made: `{str(payload['provider_calls_made']).lower()}`",
        f"- Text sent to provider: `{str(payload['text_sent_to_provider']).lower()}`",
        f"- API key value logged: `{str(payload['api_key_value_logged']).lower()}`",
        f"- Opens PROD-102: `{str(payload['opens_prod_102']).lower()}`",
        "",
        "## Boundary",
        "",
        "- Live mode requires `--live` and `--consent-confirmed`.",
        "- Provider config comes from `runtime/config/local/dialogue_reasoner.env`, environment variables, or explicit non-secret flags.",
        "- API key values are not written to generated evidence.",
        "- The live demo response path is not changed by this runner.",
        "",
    ]
    if payload.get("missing_config"):
        lines.append(f"- Missing config: `{', '.join(payload['missing_config'])}`")
        lines.append("")
    if payload["mode"] == "live":
        lines.extend(["## Live Results", ""])
        for case in payload["llm_results"]:
            status = "pass" if case.get("pass") else "fail"
            lines.append(f"- `{case['case_id']}`: `{status}`, latency `{case.get('latency_ms')}` ms")
    else:
        lines.extend(["## Planned Cases", ""])
        for case in payload["planned_cases"]:
            lines.append(f"- `{case['case_id']}`: prompt chars `{case['prompt_char_count']}`")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate DIALOGUE-REASONER-001 against an optional LLM provider.")
    parser.add_argument("--live", action="store_true", help="Actually call the configured provider.")
    parser.add_argument("--consent-confirmed", action="store_true", help="Confirm synthetic transcript upload is approved.")
    parser.add_argument("--api-key-env", default="DIALOGUE_REASONER_API_KEY")
    parser.add_argument("--env-file", default=None, help="Local ignored env file. Defaults to runtime/config/local/dialogue_reasoner.env.")
    parser.add_argument("--base-url", default=None, help="OpenAI-compatible chat/completions URL. Can also use DIALOGUE_REASONER_BASE_URL.")
    parser.add_argument("--model", default=None, help="Model id. Can also use DIALOGUE_REASONER_MODEL.")
    parser.add_argument("--timeout-seconds", type=float, default=12.0)
    parser.add_argument("--temperature", type=float, default=DEFAULT_REASONER_TEMPERATURE)
    parser.add_argument("--disable-json-response-format", action="store_true")
    parser.add_argument("--max-cases", type=int, default=0, help="Optional smoke limit before running the full 30 cases.")
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
