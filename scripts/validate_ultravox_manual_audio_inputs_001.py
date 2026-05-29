#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-MANUAL-AUDIO-INPUTS-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-MANUAL-AUDIO-INPUTS-001" / "report.md"
PREPARE_PATH = ROOT / "scripts" / "prepare_ultravox_manual_audio_inputs_001.py"
LOCAL_ARTIFACT_PREFIXES = (
    "local_artifacts/audio_outputs/ultravox/manual_inputs/",
    "local_artifacts/audio_outputs/ultravox/prepared_inputs/",
)
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


def git_tracked(relative_path: str) -> bool:
    completed = subprocess.run(
        ["git", "ls-files", "--error-unmatch", relative_path],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.returncode == 0


def assert_no_secret(label: str, text: str) -> None:
    match = SECRET_PATTERN.search(text)
    if match:
        fail(f"secret-like value found in {label}: {match.group(0)!r}")


def assert_local_artifact_path(value: str) -> None:
    normalized = value.replace("\\", "/")
    if not any(normalized.startswith(prefix) for prefix in LOCAL_ARTIFACT_PREFIXES):
        fail(f"manual/prepared audio path outside local_artifacts audio boundary: {value}")
    if ".." in Path(normalized).parts:
        fail(f"audio path must not contain parent traversal: {value}")
    if git_tracked(normalized):
        fail(f"audio file is tracked by Git: {value}")


def main() -> None:
    result = load_json(RESULT_PATH)
    report = REPORT_PATH.read_text(encoding="utf-8") if REPORT_PATH.is_file() else ""
    if not report:
        fail(f"missing file: {rel(REPORT_PATH)}")
    if not PREPARE_PATH.is_file():
        fail(f"missing file: {rel(PREPARE_PATH)}")
    assert_no_secret("manual audio input evidence/preparer", json.dumps(result) + report + PREPARE_PATH.read_text(encoding="utf-8"))

    if result.get("evaluation_id") != "ULTRAVOX-MANUAL-AUDIO-INPUTS-001":
        fail("unexpected manual audio input evaluation_id")
    if result.get("phase") != "4J5B":
        fail("manual audio input evidence must record phase 4J5B")
    if result.get("expected_case_count") != 2:
        fail("manual audio evidence must expect two cases")

    for key in (
        "manual_input_folder_exists",
        "conversion_attempted",
        "conversion_succeeded",
        "audio_files_committed",
        "provider_calls_made",
    ):
        if key not in result or not isinstance(result[key], bool):
            fail(f"result missing boolean field: {key}")
    for key in ("input_files_found", "prepared_case_count"):
        if key not in result or not isinstance(result[key], int) or result[key] < 0:
            fail(f"result missing non-negative integer field: {key}")
    if result.get("audio_files_committed") is not False:
        fail("audio_files_committed must stay false")
    if result.get("provider_calls_made") is not False:
        fail("manual input preparation must not make provider calls")

    for item in result.get("input_files", []):
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            fail("input_files entries must include path")
        assert_local_artifact_path(item["path"])
    for item in result.get("prepared_files", []):
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            fail("prepared_files entries must include path")
        assert_local_artifact_path(item["path"])

    if result.get("status") == "missing_manual_inputs":
        if result.get("conversion_attempted") is not False or result.get("prepared_case_count") != 0:
            fail("missing manual inputs must not attempt conversion or prepare cases")
    elif result.get("conversion_succeeded") is True:
        if result.get("prepared_case_count") != 2:
            fail("successful conversion must prepare two cases")
        if result.get("converter_used") not in {"ffmpeg", "python_wave_pcm_copy", "python_wave_pcm_integer_resample", "torchaudio"}:
            fail("unexpected converter_used for successful conversion")
        for item in result.get("prepared_files", []):
            if item.get("sample_rate") != 48000:
                fail("prepared sample_rate must be 48000")
            if item.get("channels") != 1:
                fail("prepared channels must be mono")
            if item.get("sample_width") != 2:
                fail("prepared sample_width must be 2 bytes")
            if not item.get("file_hash"):
                fail("prepared file hash is required")
    else:
        blockers = result.get("blockers")
        if not isinstance(blockers, list) or not blockers:
            fail("failed conversion must record blockers")

    required_report_lines = [
        "Manual input folder exists:",
        "Input files found:",
        "Prepared case count:",
        "Conversion attempted:",
        "Conversion succeeded:",
        "Converter used:",
        "Audio files committed: `false`",
        "Provider calls made: `false`",
    ]
    for line in required_report_lines:
        if line not in report:
            fail(f"manual audio input report missing line: {line}")

    print("ULTRAVOX manual audio input validation passed.")


if __name__ == "__main__":
    main()
