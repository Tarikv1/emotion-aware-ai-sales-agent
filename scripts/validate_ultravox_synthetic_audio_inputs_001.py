#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-SYNTHETIC-AUDIO-INPUTS-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-SYNTHETIC-AUDIO-INPUTS-001" / "report.md"
GENERATOR_PATH = ROOT / "scripts" / "generate_ultravox_synthetic_audio_inputs_001.py"
LOCAL_ARTIFACT_PREFIX = "local_artifacts/audio_outputs/ultravox/synthetic_inputs/"
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


def git_tracked(relative_path: str) -> bool:
    completed = subprocess.run(
        ["git", "ls-files", "--error-unmatch", relative_path],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.returncode == 0


def assert_local_artifact_path(value: str) -> None:
    normalized = value.replace("\\", "/")
    if not normalized.startswith(LOCAL_ARTIFACT_PREFIX):
        fail(f"audio output path must stay under {LOCAL_ARTIFACT_PREFIX}: {value}")
    if ".." in Path(normalized).parts:
        fail(f"audio output path must not contain parent traversal: {value}")


def main() -> None:
    result = load_json(RESULT_PATH)
    report = REPORT_PATH.read_text(encoding="utf-8") if REPORT_PATH.is_file() else ""
    if not report:
        fail(f"missing file: {rel(REPORT_PATH)}")
    if not GENERATOR_PATH.is_file():
        fail(f"missing file: {rel(GENERATOR_PATH)}")
    assert_no_secret("audio input evidence/generator", json.dumps(result) + report + GENERATOR_PATH.read_text(encoding="utf-8"))

    if result.get("evaluation_id") != "ULTRAVOX-SYNTHETIC-AUDIO-INPUTS-001":
        fail("unexpected synthetic audio input evaluation_id")
    if result.get("phase") != "4J5":
        fail("synthetic audio input evidence must record phase 4J5")
    for key in ("generation_attempted", "generation_succeeded", "audio_files_committed", "provider_calls_made"):
        if key not in result or not isinstance(result[key], bool):
            fail(f"result missing boolean field: {key}")
    if result.get("audio_files_committed") is not False:
        fail("audio_files_committed must stay false")
    if result.get("provider_calls_made") is not False:
        fail("input generation must not make provider calls")

    outputs = result.get("output_paths")
    if not isinstance(outputs, list):
        fail("output_paths must be a list")
    for output in outputs:
        if not isinstance(output, str):
            fail("output_paths entries must be strings")
        assert_local_artifact_path(output)
        if git_tracked(output.replace("\\", "/")):
            fail(f"audio output is tracked by Git: {output}")

    if result.get("generation_succeeded") is True:
        if result.get("generator_used") not in {"windows_system_speech_sapi", "windows_sapi_spvoice"}:
            fail("successful generation must identify the local Windows TTS generator")
        if result.get("sample_rate") != 48000:
            fail("synthetic audio sample_rate must be 48000")
        if len(outputs) != 2:
            fail("two synthetic audio inputs are required")
        if not isinstance(result.get("duration_seconds"), list) or len(result["duration_seconds"]) != 2:
            fail("duration_seconds must contain two values")
        if not isinstance(result.get("file_hashes"), list) or len(result["file_hashes"]) != 2:
            fail("file_hashes must contain two values")
    else:
        if not result.get("blocker"):
            fail("failed generation must record blocker")

    required_report_lines = [
        "Generation attempted:",
        "Generation succeeded:",
        "Generator used:",
        "Audio files committed: `false`",
        "Provider calls made: `false`",
    ]
    for line in required_report_lines:
        if line not in report:
            fail(f"synthetic audio input report missing line: {line}")

    print("ULTRAVOX synthetic audio input validation passed.")


if __name__ == "__main__":
    main()
