#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_resp_003_bilingual_live_tts_ab.py"
TMP_DIR = ROOT / ".tmp" / "resp-003-bilingual-live-tts-ab-validation"
TMP_JSON = TMP_DIR / "result.json"
TMP_REPORT = TMP_DIR / "report.md"
TMP_AUDIO_DIR = TMP_DIR / "audio"

SECRET_PATTERN = re.compile(
    r"(sk_car_[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|CARTESIA_API_KEY\s*=\s*[^\s]+|ELEVENLABS_API_KEY\s*=\s*[^\s]+|OPENAI_API_KEY\s*=\s*[^\s]+|Authorization:\s*Bearer\s+[A-Za-z0-9]|X-API-Key\s*[:=]\s*[A-Za-z0-9]|xi-api-key\s*[:=]\s*[A-Za-z0-9])"
)

SECRET_VALUES = {
    "ELEVENLABS_API_KEY": "TEST_ELEVENLABS_VALUE_MUST_NOT_APPEAR",
    "CARTESIA_API_KEY": "TEST_CARTESIA_VALUE_MUST_NOT_APPEAR",
    "ELEVENLABS_VOICE_ID_DE": "test-eleven-de-voice-id-must-not-appear",
    "ELEVENLABS_VOICE_ID_EN": "test-eleven-en-voice-id-must-not-appear",
    "CARTESIA_VOICE_ID_DE": "test-cartesia-de-voice-id-must-not-appear",
    "CARTESIA_VOICE_ID_EN": "test-cartesia-en-voice-id-must-not-appear",
}


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(SECRET_VALUES)
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env, timeout=60)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_dry_run_payload(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    assert_condition(payload["experiment_id"] == "RESP-003-bilingual-live-tts-ab", payload)
    assert_condition(summary["case_count"] == 6, summary)
    assert_condition(summary["matched_pair_count"] == 3, summary)
    assert_condition(summary["english_case_count"] == 3, summary)
    assert_condition(summary["german_case_count"] == 3, summary)
    assert_condition(summary["provider_count"] == 1, summary)
    assert_condition(summary["ab_variant_count"] == 12, summary)
    assert_condition(summary["plain_variant_count"] == 6, summary)
    assert_condition(summary["shaped_variant_count"] == 6, summary)
    assert_condition(summary["live_call_requested"] is False, summary)
    assert_condition(summary["api_calls_made"] == 0, summary)
    assert_condition(summary["audio_files_created"] == 0, summary)
    assert_condition(summary["fallback_count"] == 12, summary)
    assert_condition(summary["customer_audio_uploaded"] is False, summary)
    assert_condition(summary["voice_cloning_used"] is False, summary)
    assert_condition(summary["human_listening_review_recorded"] is False, summary)
    assert_condition(summary["quality_claim_allowed"] is False, summary)
    assert_condition(summary["all_shaped_inputs_differ_from_plain"] is True, summary)

    by_pair: dict[str, set[str]] = {}
    for case in payload["cases"]:
        by_pair.setdefault(case["pair_id"], set()).add(case["language"])
        assert_condition(case["runtime_voice_delivery_id"] == "RESP-002-runtime-voice-delivery", case)
        assert_condition(case["runtime_tts_delivery_id"] == "RESP-003-runtime-live-tts", case)
        assert_condition(case["provider_rendering_changed"] is True, case)
        assert_condition(len(case["ab_results"]) == 2, case)
        by_variant = {result["variant_kind"]: result for result in case["ab_results"]}
        assert_condition(set(by_variant) == {"plain_guarded", "shaped_runtime"}, by_variant)
        plain = by_variant["plain_guarded"]
        shaped = by_variant["shaped_runtime"]
        assert_condition(plain["tts_input_text"] == case["final_response"], plain)
        assert_condition(shaped["tts_input_text"] == case["runtime_tts_input_text"], shaped)
        assert_condition(shaped["tts_input_text"] != plain["tts_input_text"], case)
        assert_condition(shaped["tts_input_source"] == "provider_rendered_text", shaped)
        assert_condition(shaped["provider_rendering_used"] is True, shaped)
        for result in case["ab_results"]:
            assert_condition(result["api_call_made"] is False, result)
            assert_condition(result["audio_file_created"] is False, result)
            assert_condition(result["fallback_used"] is True, result)
            assert_condition(result["fallback_reason"] == "dry-run-mode", result)
            assert_condition(result["generated_text_sent_to_provider"] is False, result)
            assert_condition(result["customer_audio_uploaded"] is False, result)
            assert_condition(result["voice_cloning_used"] is False, result)
            assert_condition(result["api_key_value_logged"] is False, result)
            assert_condition(result["voice_id_value_logged"] is False, result)
            assert_condition("<redacted" in json.dumps(result["request_preview"], ensure_ascii=False), result)
    assert_condition(by_pair == {"objection": {"de", "en"}, "trust": {"de", "en"}, "next_step": {"de", "en"}}, by_pair)


def validate_forced_missing_key() -> None:
    out_path = TMP_DIR / "forced-missing-result.json"
    report_path = TMP_DIR / "forced-missing-report.md"
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--provider",
            "elevenlabs",
            "--live",
            "--force-key-missing",
            "--audio-dir",
            str(TMP_AUDIO_DIR),
            "--out",
            str(out_path),
            "--report-out",
            str(report_path),
        ]
    )
    assert_condition(completed.returncode == 0, completed.stderr)
    payload = load_json(out_path)
    summary = payload["summary"]
    assert_condition(summary["live_call_requested"] is True, summary)
    assert_condition(summary["api_calls_made"] == 0, summary)
    assert_condition(summary["audio_files_created"] == 0, summary)
    assert_condition(summary["fallback_count"] == 12, summary)
    for case in payload["cases"]:
        for result in case["ab_results"]:
            assert_condition(result["fallback_reason"] == "forced-key-missing", result)
            assert_condition(result["generated_text_sent_to_provider"] is False, result)


def main() -> None:
    assert_condition(RUNNER.exists(), "RESP-003 bilingual live TTS A/B runner is missing.")
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--provider",
            "elevenlabs",
            "--audio-dir",
            str(TMP_AUDIO_DIR),
            "--out",
            str(TMP_JSON),
            "--report-out",
            str(TMP_REPORT),
        ]
    )
    assert_condition(completed.returncode == 0, completed.stderr)
    assert_condition(TMP_JSON.exists(), "RESP-003 bilingual A/B JSON was not created.")
    assert_condition(TMP_REPORT.exists(), "RESP-003 bilingual A/B report was not created.")

    payload = load_json(TMP_JSON)
    validate_dry_run_payload(payload)
    first_payload_text = TMP_JSON.read_text(encoding="utf-8")
    completed_again = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--provider",
            "elevenlabs",
            "--audio-dir",
            str(TMP_AUDIO_DIR),
            "--out",
            str(TMP_JSON),
            "--report-out",
            str(TMP_REPORT),
        ]
    )
    assert_condition(completed_again.returncode == 0, completed_again.stderr)
    assert_condition(first_payload_text == TMP_JSON.read_text(encoding="utf-8"), "Dry-run output should be deterministic.")

    validate_forced_missing_key()
    combined_output = (
        json.dumps(load_json(TMP_JSON), ensure_ascii=False)
        + TMP_REPORT.read_text(encoding="utf-8")
        + completed.stdout
        + completed.stderr
    )
    assert_condition("Plain guarded" in TMP_REPORT.read_text(encoding="utf-8"), "Report should describe plain guarded text.")
    assert_condition("RESP-002 shaped" in TMP_REPORT.read_text(encoding="utf-8"), "Report should describe RESP-002 shaped text.")
    for value in SECRET_VALUES.values():
        assert_condition(value not in combined_output, f"Secret test value leaked: {value}")
    match = SECRET_PATTERN.search(combined_output)
    if match is not None:
        raise AssertionError(f"Potential secret-like value found in RESP-003 bilingual A/B output: {match.group(0)!r}")
    print("RESP-003 bilingual live TTS A/B validation passed.")


if __name__ == "__main__":
    main()
