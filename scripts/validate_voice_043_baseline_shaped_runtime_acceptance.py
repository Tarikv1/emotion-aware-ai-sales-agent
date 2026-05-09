#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_voice_043_baseline_shaped_runtime_acceptance.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "voice-043-baseline-shaped-runtime-acceptance.json"
DOC_PATH = ROOT / "docs" / "product" / "VOICE_043_BASELINE_SHAPED_RUNTIME_ACCEPTANCE.md"
TMP_DIR = ROOT / ".tmp" / "voice-043-baseline-shaped-runtime-acceptance-validation"
TMP_JSON = TMP_DIR / "result.json"
TMP_REPORT = TMP_DIR / "report.md"
TMP_AUDIO_DIR = TMP_DIR / "audio"


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_payload(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    assert_condition(payload["experiment_id"] == "VOICE-043-baseline-shaped-runtime-acceptance", payload)
    assert_condition(summary["case_count"] == 3, summary)
    assert_condition(summary["baseline_shaped_runtime_preferred"] is True, summary)
    assert_condition(summary["private_pattern_profile_promoted"] is False, summary)
    assert_condition(summary["voice_private_pattern_profile_applied_count"] == 0, summary)
    assert_condition(summary["provider_calls_made"] is False, summary)
    assert_condition(summary["audio_files_created"] == 0, summary)
    assert_condition(summary["customer_audio_uploaded"] is False, summary)
    assert_condition(summary["voice_cloning_used"] is False, summary)
    assert_condition(summary["raw_audio_read"] is False, summary)
    assert_condition(summary["validation_passed"] is True, summary)

    languages = {case["language"] for case in payload["cases"]}
    assert_condition(languages == {"en", "de"}, languages)

    for case in payload["cases"]:
        profile = case["voice_private_pattern_profile"]
        tts = case["tts_delivery"]
        settings = case["provider_rendering"]["voice_settings"]
        assert_condition(profile["enabled"] is False, profile)
        assert_condition(profile["applied"] is False, profile)
        assert_condition(profile["blocked_reason"] == "profile_disabled", profile)
        assert_condition(settings.get("style") == 0.0, settings)
        assert_condition(tts["provider_calls_made"] is False, tts)
        assert_condition(tts["audio_file_created"] is False, tts)
        assert_condition(tts["customer_audio_uploaded"] is False, tts)
        assert_condition(tts["voice_cloning_used"] is False, tts)
        assert_condition(case["validation"]["passed"] is True, case["validation"])

    protected = next(case for case in payload["cases"] if case["case_id"] == "voice-043-protected-do-not-call-baseline-lock")
    assert_condition(protected["segment_type"] == "do_not_call", protected)
    assert_condition(protected["provider_rendering"]["protected_segment_provider_tag_count"] == 0, protected)
    assert_condition(protected["provider_rendering"]["rendered_text"] == protected["final_response"], protected)


def main() -> None:
    assert_condition(DOC_PATH.exists(), "VOICE-043 product doc is missing.")
    assert_condition(CASE_PATH.exists(), "VOICE-043 case file is missing.")
    assert_condition(RUNNER.exists(), "VOICE-043 runner is missing.")
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--audio-dir",
            str(TMP_AUDIO_DIR),
            "--out",
            str(TMP_JSON),
            "--report-out",
            str(TMP_REPORT),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    assert_condition(TMP_JSON.exists(), "VOICE-043 JSON result was not written.")
    assert_condition(TMP_REPORT.exists(), "VOICE-043 Markdown report was not written.")
    validate_payload(load_json(TMP_JSON))
    print("VOICE-043 baseline shaped runtime acceptance validation passed.")


if __name__ == "__main__":
    main()
