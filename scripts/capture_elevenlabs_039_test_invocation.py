#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

try:
    from apply_elevenlabs_038_end_call_terminal_control import json_request
except ImportError as exc:  # pragma: no cover - only reachable from an unusual import path
    raise SystemExit(f"error: cannot import the existing ElevenLabs API helper: {exc}") from exc


ROOT = Path(__file__).resolve().parents[1]
API_KEY_ENV_VAR = "ELEVENLABS_API_KEY"
EXPECTED_AGENT_ID = "agent_7801kt0g32zxf4f8x5zkykj7syty"
CHECKPOINT_ID = "ELEVENLABS-039-end-call-edge-case-hardening"

EXPECTED_SYNTHETIC_EMAILS = {
    "owner@harborpetgrooming.com",
    "owner@clearpathtutoring.com",
}
EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")
SENSITIVE_KEY_RE = re.compile(
    r"(?:access|authorization|cookie|header|password|secret|token|api[_-]?key|phone|customer|user_id|workspace)",
    re.IGNORECASE,
)

RUN_FIELDS = {
    "test_run_id",
    "test_invocation_id",
    "agent_id",
    "test_id",
    "test_name",
    "status",
    "condition_result",
    "evaluator_rationale",
    "evaluation_rationale",
    "scenario",
    "simulation_scenario",
    "success_condition",
    "success_conditions",
    "agent_responses",
    "test_info",
}
TOOL_CALL_FIELDS = {
    "request_id",
    "tool_name",
    "name",
    "type",
    "params_as_json",
    "tool_has_been_called",
    "status",
}
TOOL_RESULT_FIELDS = {
    "request_id",
    "tool_name",
    "name",
    "type",
    "result_value",
    "result",
    "response",
    "output",
    "status",
    "success",
    "is_error",
    "is_blocked",
    "tool_has_been_called",
    "tool_latency_secs",
    "error_type",
    "raw_error_message",
    "error",
    "blocked",
}
EVENT_FIELDS = {
    "role",
    "message",
    "original_message",
    "time",
    "time_in_call_secs",
    "source",
    "source_medium",
    "tool_calls",
    "tool_results",
    "interrupted",
}


def redact_text(value: str) -> str:
    def redact_email(match: re.Match[str]) -> str:
        email = match.group(0)
        return email if email.lower() in EXPECTED_SYNTHETIC_EMAILS else "[REDACTED_EMAIL]"

    value = EMAIL_RE.sub(redact_email, value)
    return PHONE_RE.sub("[REDACTED_PHONE]", value)


def sanitize_nested(value: Any, *, key_hint: str = "") -> Any:
    if isinstance(value, dict):
        clean: dict[str, Any] = {}
        for raw_key, raw_item in value.items():
            key = str(raw_key)
            if SENSITIVE_KEY_RE.search(key) and key not in {
                "system__reason",
                "system__message_to_speak",
            }:
                continue
            clean[key] = sanitize_nested(raw_item, key_hint=key)
        return clean
    if isinstance(value, list):
        return [sanitize_nested(item, key_hint=key_hint) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


def sanitize_params_as_json(value: Any) -> Any:
    if not isinstance(value, str):
        return sanitize_nested(value, key_hint="params_as_json")
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return redact_text(value)
    return json.dumps(sanitize_nested(parsed), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sanitize_tool_call(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"value": sanitize_nested(value)}
    clean: dict[str, Any] = {}
    for key in TOOL_CALL_FIELDS:
        if key in value:
            item = value[key]
            clean[key] = sanitize_params_as_json(item) if key == "params_as_json" else sanitize_nested(item, key_hint=key)
    if "tool_name" not in clean and "name" not in clean:
        for alias in ("tool", "function_name"):
            if alias in value:
                clean["tool_name"] = redact_text(str(value[alias]))
                break
    return clean


def sanitize_tool_result(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"result": sanitize_nested(value)}
    return {
        key: sanitize_nested(value[key], key_hint=key)
        for key in TOOL_RESULT_FIELDS
        if key in value
    }


def sanitize_agent_response(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("agent_responses must contain objects")
    clean: dict[str, Any] = {}
    for key in EVENT_FIELDS:
        if key not in value:
            continue
        item = value[key]
        if key == "time_in_call_secs":
            if "time" not in clean:
                clean["time"] = item
        elif key == "tool_calls":
            clean[key] = [sanitize_tool_call(entry) for entry in item] if isinstance(item, list) else []
        elif key == "tool_results":
            clean[key] = [sanitize_tool_result(entry) for entry in item] if isinstance(item, list) else []
        elif key in {"message", "original_message", "source", "source_medium"} and isinstance(item, str):
            clean[key] = redact_text(item)
        else:
            clean[key] = sanitize_nested(item, key_hint=key)
    return clean


def first_value(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None


def test_info_value(run: dict[str, Any], *keys: str) -> Any:
    info = run.get("test_info")
    candidates = [run.get(key) for key in keys]
    if isinstance(info, dict):
        candidates.extend(info.get(key) for key in keys)
    return first_value(*candidates)


def agent_responses_value(run: dict[str, Any], info: dict[str, Any], *, test_id: str) -> list[Any]:
    if "agent_responses" in run:
        responses = run["agent_responses"]
    elif "agent_responses" in info:
        responses = info["agent_responses"]
    else:
        raise ValueError(f"{test_id or 'run'} agent_responses must be present")
    if not isinstance(responses, list):
        raise ValueError(f"{test_id or 'run'} agent_responses must be a list")
    return responses


def sanitized_result_groups(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    groups: list[dict[str, Any]] = []
    for group in raw:
        if not isinstance(group, dict):
            continue
        clean: dict[str, Any] = {}
        for key in ("test_id", "test_name", "workflow_node_id"):
            if key in group:
                clean[key] = redact_text(str(group[key]))
        buckets = group.get("buckets")
        if isinstance(buckets, list):
            clean["buckets"] = []
            for bucket in buckets:
                if not isinstance(bucket, dict):
                    continue
                clean["buckets"].append(
                    {
                        key: sanitize_nested(bucket[key], key_hint=key)
                        for key in ("test_run_ids", "title", "reason", "status")
                        if key in bucket
                    }
                )
        groups.append(clean)
    return groups


def sanitize_run(run: Any, *, result_rationale_by_test_id: dict[str, str]) -> dict[str, Any]:
    if not isinstance(run, dict):
        raise ValueError("test_runs must contain objects")
    provider_test_id = str(run.get("test_id", ""))
    test_name = str(first_value(run.get("test_name"), provider_test_id) or "")
    test_id = test_name.rsplit("::", 1)[-1] if test_name.startswith(f"{CHECKPOINT_ID}::") else provider_test_id
    info = run.get("test_info") if isinstance(run.get("test_info"), dict) else {}
    responses = agent_responses_value(run, info, test_id=test_id)

    models: dict[str, Any] = {}
    for key in (
        "simulated_user_model",
        "evaluation_model",
        "user_model",
        "evaluator_model",
        "model",
    ):
        value = test_info_value(run, key)
        if value not in (None, "", [], {}):
            models[key] = sanitize_nested(value, key_hint=key)
    for key in ("models", "model_config"):
        value = test_info_value(run, key)
        if isinstance(value, dict):
            models[key] = sanitize_nested(value, key_hint=key)

    condition_result = run.get("condition_result")
    rationale = first_value(
        run.get("evaluator_rationale"),
        run.get("evaluation_rationale"),
        condition_result.get("rationale") if isinstance(condition_result, dict) else None,
        condition_result.get("reason") if isinstance(condition_result, dict) else None,
        result_rationale_by_test_id.get(test_id),
    )
    clean: dict[str, Any] = {
        "test_run_id": first_value(run.get("test_run_id"), run.get("run_id")),
        "test_invocation_id": first_value(run.get("test_invocation_id"), run.get("invocation_id")),
        "agent_id": first_value(run.get("agent_id"), EXPECTED_AGENT_ID),
        "test_id": test_id,
        "provider_test_id": provider_test_id,
        "test_name": test_name,
        "scenario": first_value(
            run.get("scenario"),
            run.get("simulation_scenario"),
            info.get("scenario"),
            info.get("simulation_scenario"),
        ),
        "success_conditions": first_value(
            run.get("success_conditions"),
            run.get("success_condition"),
            info.get("success_conditions"),
            info.get("success_condition"),
        ),
        "models": models,
        "status": run.get("status"),
        "condition_result": sanitize_nested(condition_result),
        "evaluator_rationale": redact_text(str(rationale)) if rationale is not None else None,
        "agent_responses": [sanitize_agent_response(item) for item in responses],
    }
    return {
        key: sanitize_nested(value, key_hint=key)
        for key, value in clean.items()
    }


def build_sanitized_payload(raw: dict[str, Any], invocation_id: str) -> dict[str, Any]:
    raw_agent_id = first_value(raw.get("agent_id"), raw.get("agent", {}).get("agent_id") if isinstance(raw.get("agent"), dict) else None)
    if raw_agent_id != EXPECTED_AGENT_ID:
        raise ValueError(f"refusing unexpected agent id {raw_agent_id!r}; expected {EXPECTED_AGENT_ID}")
    raw_runs = raw.get("test_runs")
    if not isinstance(raw_runs, list):
        raise ValueError("provider response is missing test_runs")

    rationale_by_test_id: dict[str, str] = {}
    for group in raw.get("result_groups", []) if isinstance(raw.get("result_groups"), list) else []:
        if not isinstance(group, dict):
            continue
        test_id = str(group.get("test_id", ""))
        buckets = group.get("buckets")
        if test_id and isinstance(buckets, list) and buckets:
            first_bucket = buckets[0]
            if isinstance(first_bucket, dict) and first_bucket.get("reason"):
                rationale_by_test_id[test_id] = str(first_bucket["reason"])

    return {
        "checkpoint_id": CHECKPOINT_ID,
        "invocation_id": invocation_id,
        "agent_id": EXPECTED_AGENT_ID,
        "test_runs": [sanitize_run(run, result_rationale_by_test_id=rationale_by_test_id) for run in raw_runs],
        "result_groups": sanitized_result_groups(raw.get("result_groups")),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture one ElevenLabs ELEVENLABS-039 test invocation read-only.")
    parser.add_argument("--invocation-id", required=True, help="ElevenLabs test invocation ID")
    parser.add_argument("--output", required=True, type=Path, help="Required sanitized JSON output path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    api_key = os.environ.get(API_KEY_ENV_VAR)
    if not api_key:
        print(f"error: {API_KEY_ENV_VAR} is required", file=sys.stderr)
        return 2
    invocation_id = str(args.invocation_id).strip()
    if not invocation_id:
        print("error: --invocation-id must not be empty", file=sys.stderr)
        return 2

    try:
        response = json_request(
            "GET",
            f"/v1/convai/test-invocations/{quote(invocation_id, safe='')}",
            api_key=api_key,
        )
        raw = response.get("response")
        if not isinstance(raw, dict):
            raise ValueError("provider response must be a JSON object")
        payload = build_sanitized_payload(raw, invocation_id)
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        output = {
            "captured_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "payload_sha256": hashlib.sha256(canonical).hexdigest(),
            "payload": payload,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(output, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"status": "captured", "invocation_id": invocation_id, "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
