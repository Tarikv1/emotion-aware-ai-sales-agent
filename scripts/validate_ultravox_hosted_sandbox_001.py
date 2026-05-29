#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "run_ultravox_hosted_sandbox_001.py"
CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_hosted_backend_config.json"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-HOSTED-SANDBOX-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-HOSTED-SANDBOX-001" / "report.md"

SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|u[a-z]?v[A-Za-z0-9_-]{20,}|ULTRAVOX_API_KEY\s*=\s*[^\s]+|Authorization:\s*Bearer\s+[A-Za-z0-9]|X-API-Key:\s*[A-Za-z0-9])"
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


def gates_enabled() -> bool:
    return (
        os.environ.get("ENABLE_ULTRAVOX_SANDBOX") == "1"
        and os.environ.get("LOCAL_ULTRAVOX_ALLOW_PROVIDER_CALLS") == "1"
        and bool(os.environ.get("ULTRAVOX_API_KEY"))
    )


def assert_no_secret_patterns(text: str) -> None:
    match = SECRET_PATTERN.search(text)
    if match:
        fail(f"secret-like token found: {match.group(0)!r}")


def assert_no_audio_or_model_artifacts() -> None:
    output_dir = RESULT_PATH.parent
    if not output_dir.exists():
        return
    forbidden = {".wav", ".mp3", ".flac", ".m4a", ".ogg", ".gguf", ".safetensors", ".pt", ".pth", ".bin"}
    found = [rel(path) for path in output_dir.rglob("*") if path.suffix.lower() in forbidden]
    if found:
        fail(f"hosted sandbox evidence must not contain audio/model artifacts: {found}")


def main() -> None:
    for path in (SCRIPT_PATH, CONFIG_PATH, RESULT_PATH, REPORT_PATH):
        if not path.is_file():
            fail(f"required hosted sandbox artifact missing: {rel(path)}")

    config = load_json(CONFIG_PATH)
    result = load_json(RESULT_PATH)
    report_text = REPORT_PATH.read_text(encoding="utf-8")
    assert_no_secret_patterns(json.dumps(config) + json.dumps(result) + report_text)

    if result.get("evaluation_id") != "ULTRAVOX-HOSTED-SANDBOX-001":
        fail("unexpected hosted sandbox evaluation_id")
    if result.get("outbound_phone_calls_made") is not False:
        fail("hosted sandbox must not place outbound phone calls")
    if result.get("real_customer_data_used") is not False:
        fail("hosted sandbox must not use real customer data")
    if result.get("raw_private_audio_or_transcripts_used") is not False:
        fail("hosted sandbox must not use raw private audio/transcripts")
    if result.get("audio_committed") is not False:
        fail("hosted sandbox must not commit audio")
    if result.get("model_weights_downloaded") is not False:
        fail("hosted sandbox must not download model weights")
    if result.get("live_wiring_allowed") is not False:
        fail("hosted sandbox must keep live wiring disabled")
    if result.get("production_call_allowed") is not False:
        fail("hosted sandbox must keep production calls disabled")
    if result.get("runtime_behavior_changed") is not False:
        fail("hosted sandbox must not change runtime behavior")
    if result.get("response_text_changed") is not False:
        fail("hosted sandbox must not change canonical response text")

    provider_call_made = result.get("provider_call_made")
    if not gates_enabled():
        if result.get("run_status") != "not_run":
            fail("without env gates, hosted sandbox must record run_status not_run")
        if provider_call_made is not False:
            fail("without env gates, hosted sandbox must not make provider calls")
        if "env gates were not enabled" not in result.get("blocker", ""):
            fail("not_run evidence must include a clear env-gate blocker")
    else:
        if result.get("run_status") not in {"provider_run", "blocked"}:
            fail("with env gates, hosted sandbox must either run provider sandbox or record a blocker")
        if result.get("run_status") == "blocked" and not result.get("blocker"):
            fail("blocked hosted sandbox must include a clear blocker")

    if config.get("provider_calls_allowed_by_default") is not False:
        fail("config must block provider calls by default")
    if config.get("provider_calls_allowed_only_with_env_gates") is not True:
        fail("config must require env gates for provider calls")

    assert_no_audio_or_model_artifacts()
    if "Provider call made: `false`" not in report_text and not provider_call_made:
        fail("hosted sandbox report must state no provider call was made")
    print("ULTRAVOX hosted sandbox validation passed.")


if __name__ == "__main__":
    main()
