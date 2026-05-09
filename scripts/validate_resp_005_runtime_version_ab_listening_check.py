#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_resp_005_runtime_version_ab_listening_check.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "resp-005-runtime-version-ab-listening-check.json"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "RESP-005-runtime-version-ab-listening-check" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "RESP-005-runtime-version-ab-listening-check" / "report.md"
REVIEW_PATH = ROOT / "research" / "experiments" / "generated" / "RESP-005-runtime-version-ab-listening-check" / "human-listening-review.md"

SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|sk_car_[A-Za-z0-9_-]{20,}|ELEVENLABS_API_KEY\s*=\s*[^\s]+|CARTESIA_API_KEY\s*=\s*[^\s]+|xi-api-key\s*[:=]\s*[A-Za-z0-9]|X-API-Key\s*[:=]\s*[A-Za-z0-9])"
)


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=90)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    assert_condition(RUNNER.exists(), "RESP-005 runtime version A/B runner is missing.")
    assert_condition(CASE_PATH.exists(), "RESP-005 runtime version A/B case file is missing.")

    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--cases",
            str(CASE_PATH),
            "--out",
            str(RESULT_PATH),
            "--report-out",
            str(REPORT_PATH),
            "--review-out",
            str(REVIEW_PATH),
        ]
    )
    assert_condition(completed.returncode == 0, f"Runner failed. stdout={completed.stdout!r} stderr={completed.stderr!r}")
    assert_condition(RESULT_PATH.exists(), "RESP-005 result JSON was not written.")
    assert_condition(REPORT_PATH.exists(), "RESP-005 report was not written.")
    assert_condition(REVIEW_PATH.exists(), "RESP-005 human review sheet was not written.")

    payload = load_json(RESULT_PATH)
    report = REPORT_PATH.read_text(encoding="utf-8")
    review = REVIEW_PATH.read_text(encoding="utf-8")
    summary = payload["summary"]

    assert_condition(payload["experiment_id"] == "RESP-005-runtime-version-ab-listening-check", payload)
    assert_condition(summary["case_count"] == 1, summary)
    assert_condition(summary["variant_count"] == 2, summary)
    assert_condition(summary["same_question_for_all_variants"] is True, summary)
    assert_condition(summary["old_runtime_variant_count"] == 1, summary)
    assert_condition(summary["new_runtime_variant_count"] == 1, summary)
    assert_condition(summary["minimum_tts_input_chars"] >= 180, summary)
    assert_condition(summary["live_call_requested"] is False, summary)
    assert_condition(summary["customer_audio_uploaded"] is False, summary)
    assert_condition(summary["voice_cloning_used"] is False, summary)
    assert_condition(summary["synthetic_prompts_only"] is True, summary)
    assert_condition(summary["quality_claim_allowed"] is False, summary)
    assert_condition(summary["raw_secret_values_logged"] is False, summary)

    case = payload["cases"][0]
    assert_condition(case["question"] == case["variants"][0]["question"] == case["variants"][1]["question"], case)
    variants = {variant["variant_kind"]: variant for variant in case["variants"]}
    assert_condition(set(variants) == {"old_plain_guarded", "new_shaped_runtime"}, variants)
    old = variants["old_plain_guarded"]
    new = variants["new_shaped_runtime"]
    assert_condition(old["tts_input_text"] != new["tts_input_text"], case)
    assert_condition(old["provider_rendering_used"] is False, old)
    assert_condition(new["provider_rendering_used"] is True, new)
    assert_condition("old runtime" in old["label"].lower(), old)
    assert_condition("new runtime" in new["label"].lower(), new)
    assert_condition(new["source_checkpoint"] == "RESP-002/VOICE-044 shaped runtime", new)
    assert_condition(old["source_checkpoint"] == "RESP-001 guarded final_response", old)
    assert_condition(new["voice_settings"] != old["voice_settings"], case)
    assert_condition(new["tts_input_chars"] >= 180, new)
    assert_condition(old["tts_input_chars"] >= 180, old)
    assert_condition("?" in case["question"], case)
    assert_condition("send" in case["question"].lower(), case)
    assert_condition("same question" in report.lower(), report)
    assert_condition("more complex speaking" in report.lower(), report)
    assert_condition("old_plain_guarded" in review, review)
    assert_condition("new_shaped_runtime" in review, review)

    for variant in case["variants"]:
        assert_condition(variant["api_key_value_logged"] is False, variant)
        assert_condition(variant["voice_id_value_logged"] is False, variant)
        assert_condition(variant["customer_audio_uploaded"] is False, variant)
        assert_condition(variant["voice_cloning_used"] is False, variant)
        assert_condition(variant["generated_text_sent_to_provider"] is False, variant)
        assert_condition(variant["request_preview"]["headers"]["xi-api-key"] == "<redacted>", variant)
        assert_condition("<redacted" in json.dumps(variant["request_preview"], ensure_ascii=False), variant)
        if variant["audio_file_created"]:
            audio_path = ROOT / variant["audio_output_path"]
            assert_condition(audio_path.exists(), variant)
            assert_condition(audio_path.stat().st_size == variant["audio_byte_size"], variant)

    combined = json.dumps(payload, ensure_ascii=False) + report + review + completed.stdout + completed.stderr
    match = SECRET_PATTERN.search(combined)
    if match is not None:
        raise AssertionError(f"Potential secret-like value found: {match.group(0)!r}")

    print("RESP-005 runtime version A/B listening check validation passed.")


if __name__ == "__main__":
    main()
