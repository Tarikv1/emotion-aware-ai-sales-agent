#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_voice_021_custom_voice_comparison.py"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "voice-021-elevenlabs-custom-voice-comparison.json"
TMP_DIR = ROOT / ".tmp" / "voice-021-validation" / f"run-{uuid.uuid4().hex}"
TMP_JSON = TMP_DIR / "VOICE-021-custom-voice-comparison.json"
TMP_REPORT = TMP_DIR / "VOICE-021-custom-voice-comparison-report.md"
TMP_AUDIO_DIR = TMP_DIR / "audio"
TMP_LOCAL_VOICE_CONFIG = TMP_DIR / "voice_ids.json"

SECRET_VALUES = {
    "ELEVENLABS_API_KEY": "TEST_ELEVENLABS_VALUE_MUST_NOT_APPEAR",
    "english_v1": "test-english-v1-voice-id-must-not-appear",
    "english_v2_improved": "test-english-v2-voice-id-must-not-appear",
    "german_v1": "test-german-v1-voice-id-must-not-appear",
    "german_v2_improved": "test-german-v2-voice-id-must-not-appear",
}

SECRET_PATTERN = re.compile(
    "|".join(re.escape(value) for value in SECRET_VALUES.values())
    + r"|sk_car_[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{20,}|xi-api-key\s*[:=]\s*[A-Za-z0-9]"
)


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def write_local_voice_config() -> None:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    TMP_LOCAL_VOICE_CONFIG.write_text(
        json.dumps(
            {
                "elevenlabs": {
                    "candidates": {
                        candidate_id: {
                            "language": "de" if candidate_id.startswith("german") else "en",
                            "label": candidate_id,
                            "voice_id": voice_id,
                        }
                        for candidate_id, voice_id in SECRET_VALUES.items()
                        if candidate_id != "ELEVENLABS_API_KEY"
                    }
                }
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def run_command(args: list[str], env_values: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if env_values:
        env.update(env_values)
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env, timeout=45)


def run_voice_021(extra_args: list[str] | None = None, env_values: dict[str, str] | None = None) -> dict:
    args = [
        sys.executable,
        str(RUNNER),
        "--cases",
        str(CASES_PATH),
        "--local-voice-config",
        str(TMP_LOCAL_VOICE_CONFIG),
        "--audio-dir",
        str(TMP_AUDIO_DIR),
        "--out",
        str(TMP_JSON),
        "--report-out",
        str(TMP_REPORT),
    ]
    if extra_args:
        args.extend(extra_args)
    completed = run_command(args, env_values=env_values)
    assert_condition(completed.returncode == 0, completed.stderr)
    return json.loads(TMP_JSON.read_text(encoding="utf-8"))


def validate_payload(payload: dict, live_expected: bool, fallback_reason: str) -> None:
    summary = payload["summary"]
    expected = payload["expected"]
    assert_condition(payload["voice_milestone"] == "VOICE-021", payload["voice_milestone"])
    assert_condition(summary["candidate_count"] == expected["candidate_count"], summary)
    assert_condition(summary["script_count"] == expected["script_count"], summary)
    assert_condition(summary["comparison_group_count"] == expected["comparison_group_count"], summary)
    assert_condition(summary["result_count"] == expected["dry_run_result_count"], summary)
    assert_condition(summary["languages"] == {"de": 4, "en": 4}, summary)
    assert_condition(summary["live_call_requested"] is live_expected, summary)
    assert_condition(summary["api_calls_made"] == 0, summary)
    assert_condition(summary["audio_files_created"] == 0, summary)
    assert_condition(summary["customer_audio_uploaded"] is False, summary)
    assert_condition(summary["voice_cloning_used"] is False, summary)
    assert_condition(summary["quality_claim_allowed"] is False, summary)
    assert_condition(summary["raw_voice_ids_logged"] is False, summary)

    candidate_ids = {candidate["candidate_id"] for candidate in payload["voice_candidates"]}
    for required in {"english_v1", "english_v2_improved", "german_v1", "german_v2_improved"}:
        assert_condition(required in candidate_ids, f"Missing voice candidate: {required}")

    for result in payload["results"]:
        assert_condition(result["provider_key"] == "elevenlabs", result)
        assert_condition(result["api_key_value_logged"] is False, result)
        assert_condition(result["voice_id_value_logged"] is False, result)
        assert_condition(result["customer_audio_uploaded"] is False, result)
        assert_condition(result["voice_cloning_used"] is False, result)
        assert_condition(result["fallback_used"] is True, result)
        assert_condition(result["fallback_reason"] == fallback_reason, result)
        assert_condition(result["audio_file_created"] is False, result)
        assert_condition(result["voice_id_source"].startswith("local_voice_ids:elevenlabs.candidates."), result)
        assert_condition(result["voice_candidate_id"] in candidate_ids, result)
        assert_condition(result["voice_id_present"] is (not live_expected), result)
        assert_condition(result["tts_input_text"], result)


def assert_no_secret_text(payload: dict) -> None:
    combined = (
        json.dumps(payload, ensure_ascii=False)
        + TMP_REPORT.read_text(encoding="utf-8")
    )
    match = SECRET_PATTERN.search(combined)
    if match is not None:
        raise AssertionError(f"Potential secret or raw voice ID leaked in VOICE-021 artifact: {match.group(0)!r}")


def main() -> None:
    assert_condition(RUNNER.exists(), "VOICE-021 runner is missing.")
    assert_condition(CASES_PATH.exists(), "VOICE-021 case file is missing.")
    try:
        write_local_voice_config()

        dry_payload = run_voice_021()
        validate_payload(dry_payload, live_expected=False, fallback_reason="dry-run-mode")
        assert_no_secret_text(dry_payload)

        forced_missing_payload = run_voice_021(
            extra_args=["--live", "--force-key-missing"],
            env_values={"ELEVENLABS_API_KEY": SECRET_VALUES["ELEVENLABS_API_KEY"]},
        )
        validate_payload(forced_missing_payload, live_expected=True, fallback_reason="forced-key-missing")
        assert_no_secret_text(forced_missing_payload)

        print("VOICE-021 custom voice comparison validation passed.")
    finally:
        shutil.rmtree(TMP_DIR, ignore_errors=True)


if __name__ == "__main__":
    main()
