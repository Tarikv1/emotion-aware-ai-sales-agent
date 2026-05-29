#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-LATENCY-SETTINGS-OPTIONS-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-LATENCY-SETTINGS-OPTIONS-001" / "report.md"
AUDIT_SCRIPT_PATH = ROOT / "scripts" / "audit_ultravox_latency_settings_options_001.py"

SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|[A-Za-z0-9]{8}\.[A-Za-z0-9]{32}|ULTRAVOX_API_KEY\s*=\s*(?!\.\.\.|<redacted>|your-api-key)[^\s]+|PROJECT_ULTRAVOX_TOOL_TOKEN\s*=\s*(?!\.\.\.|<redacted>|your-token)[^\s]+|Authorization:\s*Bearer\s+[A-Za-z0-9]|X-API-Key:\s*(?!<redacted>|your-api-key)[A-Za-z0-9]|X-Project-Tool-Token:\s*(?!<redacted>|your-token)[A-Za-z0-9]|wss://[^\"'\s]+|https://voice\.ultravox\.ai/[^\"'\s]+)"
)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def fail(message: str) -> None:
    raise AssertionError(message)


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        fail(f"missing file: {rel(path)}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        fail(f"{rel(path)} must be a JSON object")
    return payload


def assert_no_secret(label: str, text: str) -> None:
    match = SECRET_PATTERN.search(text)
    if match:
        fail(f"secret-like value found in {label}: {match.group(0)!r}")


def option_map(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    options = result.get("options")
    if not isinstance(options, list) or not options:
        fail("result options must be a non-empty list")
    mapped: dict[str, dict[str, Any]] = {}
    for item in options:
        if not isinstance(item, dict):
            fail("each option must be an object")
        option_id = str(item.get("option_id") or "")
        if not option_id:
            fail("option missing option_id")
        mapped[option_id] = item
    return mapped


def main() -> None:
    result = load_json(RESULT_PATH)
    report = REPORT_PATH.read_text(encoding="utf-8") if REPORT_PATH.is_file() else ""
    script_text = AUDIT_SCRIPT_PATH.read_text(encoding="utf-8") if AUDIT_SCRIPT_PATH.is_file() else ""
    if not report:
        fail(f"missing file: {rel(REPORT_PATH)}")
    assert_no_secret("settings options audit", json.dumps(result) + report + script_text)

    if result.get("evaluation_id") != "ULTRAVOX-LATENCY-SETTINGS-OPTIONS-001":
        fail("unexpected settings options evaluation_id")
    if result.get("provider_call_made") is not False:
        fail("settings options audit must not call provider")
    if result.get("docs_fetch_performed") is not False:
        fail("settings options audit must be a static official-docs/source audit")
    if result.get("unsupported_parameters_sent_as_confirmed") is not False:
        fail("unsupported parameters must not be marked as sent/confirmed")

    sources = result.get("official_sources")
    if not isinstance(sources, list) or len(sources) < 3:
        fail("official_sources must include primary Ultravox docs")
    for source in sources:
        if not isinstance(source, dict) or not str(source.get("url", "")).startswith("https://docs.ultravox.ai/"):
            fail("all sources must be official docs.ultravox.ai URLs")

    options = option_map(result)
    required = {
        "system_prompt_brevity",
        "voice_selection",
        "initial_output_medium",
        "server_websocket_client_buffer",
        "model",
        "temperature",
        "tool_declaration",
        "response_length_control",
        "low_latency_mode",
    }
    missing = sorted(required - set(options))
    if missing:
        fail(f"missing option audits: {missing}")

    valid_classes = {"supported_now", "supported_but_needs_value", "unknown", "not_supported", "not_safe"}
    for option_id, option in options.items():
        if option.get("classification") not in valid_classes:
            fail(f"{option_id} has invalid classification")
        if not option.get("evidence"):
            fail(f"{option_id} missing evidence")
        if option.get("sent_in_optimized_payload") is True and option.get("classification") not in {"supported_now", "supported_but_needs_value"}:
            fail(f"{option_id} cannot be sent with classification {option.get('classification')}")

    if options["low_latency_mode"].get("classification") not in {"unknown", "not_supported"}:
        fail("low-latency mode must not be treated as confirmed")
    if result.get("voice_change_possible_in_current_sandbox") is not False:
        fail("voice change must stay false unless a known Ultravox voice value exists")
    if result.get("prompt_brevity_change_possible") is not True:
        fail("prompt brevity should be classified possible")
    if result.get("response_length_constraints_supported") != "prompt_only":
        fail("response length control should be prompt-only")

    for line in (
        "Provider call made: `false`",
        "Voice change possible in current sandbox:",
        "Low-latency mode:",
        "Unsupported parameters sent as confirmed: `false`",
    ):
        if line not in report:
            fail(f"settings options report missing line: {line}")
    print("ULTRAVOX latency settings options validation passed.")


if __name__ == "__main__":
    main()
