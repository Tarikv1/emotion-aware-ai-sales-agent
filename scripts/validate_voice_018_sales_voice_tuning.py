#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_voice_018_sales_voice_tuning.py"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "voice-018-sales-voice-tuning.json"
TMP_DIR = ROOT / ".tmp" / "voice-018-validation"
TMP_JSON = TMP_DIR / "VOICE-018-sales-voice-tuning.json"
TMP_REPORT = TMP_DIR / "VOICE-018-sales-voice-tuning-report.md"

SECRET_PATTERN = re.compile(
    r"(sk_car_[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|CARTESIA_API_KEY\s*=\s*[^\s]+|ELEVENLABS_API_KEY\s*=\s*[^\s]+|OPENAI_API_KEY\s*=\s*[^\s]+|Authorization:\s*Bearer\s+[A-Za-z0-9]|X-API-Key\s*[:=]\s*[A-Za-z0-9]|xi-api-key\s*[:=]\s*[A-Za-z0-9])"
)

PROTECTED_TYPES = {
    "approved_opening",
    "campaign_qualification_question",
    "company_script",
    "required_disclosure",
    "compliance_statement",
    "legal_or_medical_boundary",
    "coverage_or_claim_boundary",
    "claim_boundary",
    "do_not_call",
    "hangup",
    "appointment_confirmation",
    "sensitive_escalation",
    "human_handoff_exact_script",
}


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, timeout=30)


def load_payload() -> dict:
    return json.loads(TMP_JSON.read_text(encoding="utf-8"))


def validate_segment_plan(case: dict, variant: dict, segment: dict) -> None:
    protected = segment["protected"] or segment["segment_type"] in PROTECTED_TYPES
    if protected:
        assert_condition(segment["source_text"] == segment["sales_tuned_text"], f"{case['case_id']} changed protected text.")
        assert_condition(segment["speed_ratio"] == 1.0, f"{case['case_id']} protected segment should keep neutral speed.")
        assert_condition(segment["emotion_intent"] == "neutral-clear", f"{case['case_id']} protected segment should be neutral-clear.")
        assert_condition(segment["pitch_intent"] == "steady-neutral", f"{case['case_id']} protected segment should keep neutral pitch.")
        assert_condition(segment["pause_compression_count"] == 0, f"{case['case_id']} protected segment should not compress pauses.")
        return

    if segment["tuned"]:
        assert_condition(1.0 <= segment["speed_ratio"] <= 1.16, f"{case['case_id']} speed out of bounds: {segment}")
        assert_condition(segment["emotion_intent"] in {
            "confident-low-pressure",
            "curious-efficient",
            "confident-practical",
            "warm-reassuring",
        }, f"{case['case_id']} missing useful emotion intent: {segment}")
        assert_condition(segment["pitch_intent"] in {
            "warm-soft",
            "slight-rise",
            "steady-confident",
            "steady-neutral",
        }, f"{case['case_id']} missing pitch intent: {segment}")
        if variant["provider_key"] == "cartesia":
            assert_condition("<speed ratio=" in segment["sales_tuned_text"], f"{case['case_id']} Cartesia tuned segment needs speed tag.")


def validate_provider_variant(case: dict, variant: dict) -> None:
    assert_condition(variant["provider_calls_made"] is False, f"{case['case_id']} should be offline.")
    assert_condition(variant["requires_api_key"] is False, f"{case['case_id']} should not require provider key.")
    assert_condition(variant["customer_audio_uploaded"] is False, f"{case['case_id']} uploaded customer audio.")
    assert_condition(variant["voice_cloning_used"] is False, f"{case['case_id']} used voice cloning.")
    assert_condition("**" not in variant["sales_tuned_text"], f"{case['case_id']} leaked debug Markdown.")
    assert_condition(variant["validation"]["passed"] is True, f"{case['case_id']} variant validation failed.")
    assert_condition(not variant["validation"]["protected_segment_text_changes"], f"{case['case_id']} protected text changed.")
    assert_condition(not variant["validation"]["speed_out_of_bounds"], f"{case['case_id']} speed out of bounds.")

    for segment in variant["segment_delivery_plan"]:
        validate_segment_plan(case, variant, segment)

    if case["prosody_cue_count"] > 0 and variant["provider_key"] == "elevenlabs":
        assert_condition(
            variant["voice_settings"].get("speed", 1.0) > 1.0,
            f"{case['case_id']} ElevenLabs tuned response should increase request speed.",
        )
    if case["prosody_cue_count"] == 0:
        assert_condition(variant["tuned_segment_count"] == 0, f"{case['case_id']} should not tune cue-free cases.")


def validate_payload(payload: dict, config: dict) -> None:
    expected = config["expected"]
    summary = payload["summary"]
    assert_condition(summary["case_count"] == expected["case_count"], summary)
    assert_condition(summary["provider_count"] == expected["provider_count"], summary)
    assert_condition(summary["sales_tuned_variant_count"] == expected["sales_tuned_variant_count"], summary)
    assert_condition(summary["tuned_segment_count"] >= expected["min_tuned_segments"], summary)
    assert_condition(summary["pause_compression_count"] >= expected["min_pause_compressions"], summary)
    assert_condition(summary["average_eligible_speed_ratio"] >= expected["min_average_eligible_speed_ratio"], summary)
    assert_condition(summary["max_speed_ratio"] <= expected["max_speed_ratio"], summary)
    assert_condition(summary["protected_segment_text_changes"] == expected["protected_segment_text_changes"], summary)
    assert_condition(summary["provider_calls_made"] is expected["provider_calls_made"], summary)
    assert_condition(summary["requires_api_key"] is expected["requires_api_key"], summary)
    assert_condition(summary["customer_audio_uploaded"] is expected["customer_audio_uploaded"], summary)
    assert_condition(summary["voice_cloning_used"] is expected["voice_cloning_used"], summary)
    assert_condition(summary["validation_failed"] == 0, summary)
    assert_condition(summary["quality_claim_allowed"] is False, summary)

    for case in payload["cases"]:
        assert_condition(len(case["sales_voice_variants"]) == 2, f"{case['case_id']} should have two provider variants.")
        for variant in case["sales_voice_variants"]:
            validate_provider_variant(case, variant)


def main() -> None:
    assert_condition(RUNNER.exists(), "VOICE-018 runner is missing.")
    assert_condition(CASES_PATH.exists(), "VOICE-018 case file is missing.")
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--cases",
            str(CASES_PATH),
            "--out",
            str(TMP_JSON),
            "--report-out",
            str(TMP_REPORT),
        ]
    )
    assert_condition(completed.returncode == 0, completed.stderr)
    assert_condition(TMP_JSON.exists(), "VOICE-018 validation JSON was not created.")
    assert_condition(TMP_REPORT.exists(), "VOICE-018 validation report was not created.")

    payload = load_payload()
    config = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    validate_payload(payload, config)

    first_payload_text = TMP_JSON.read_text(encoding="utf-8")
    completed_again = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--cases",
            str(CASES_PATH),
            "--out",
            str(TMP_JSON),
            "--report-out",
            str(TMP_REPORT),
        ]
    )
    assert_condition(completed_again.returncode == 0, completed_again.stderr)
    assert_condition(first_payload_text == TMP_JSON.read_text(encoding="utf-8"), "VOICE-018 output should be deterministic.")

    combined_output = json.dumps(load_payload(), ensure_ascii=False) + TMP_REPORT.read_text(encoding="utf-8") + completed.stdout
    match = SECRET_PATTERN.search(combined_output)
    if match is not None:
        raise AssertionError(f"Potential secret-like value found in VOICE-018 output: {match.group(0)!r}")
    print("VOICE-018 sales voice tuning validation passed.")


if __name__ == "__main__":
    main()
