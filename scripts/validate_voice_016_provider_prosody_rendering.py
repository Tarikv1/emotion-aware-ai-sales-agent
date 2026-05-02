#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_voice_016_provider_prosody_rendering.py"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "voice-016-provider-prosody-rendering.json"
TMP_DIR = ROOT / ".tmp" / "voice-016-validation"
TMP_JSON = TMP_DIR / "VOICE-016-provider-prosody-rendering.json"
TMP_REPORT = TMP_DIR / "VOICE-016-provider-prosody-rendering-report.md"

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
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True)


def validate_provider_variant(case: dict, variant: dict) -> None:
    provider = variant["provider_key"]
    assert_condition("**" not in variant["rendered_text"], f"{case['case_id']} {provider} leaked Markdown bold.")
    assert_condition(variant["api_call_made"] is False, f"{case['case_id']} {provider} should be offline.")
    assert_condition(variant["customer_audio_uploaded"] is False, f"{case['case_id']} {provider} uploaded customer audio.")
    assert_condition(variant["requires_api_key"] is False, f"{case['case_id']} {provider} should not require a key.")

    protected_segments = [
        segment
        for segment in variant["segment_renderings"]
        if segment["segment_type"] in PROTECTED_TYPES or segment["protected_reason"] is not None
    ]
    for segment in protected_segments:
        assert_condition(
            segment["rendered_text"] == segment["plain_text"],
            f"{case['case_id']} {provider} changed protected segment {segment['segment_id']}.",
        )
        assert_condition(
            not segment["provider_tags_inserted"],
            f"{case['case_id']} {provider} inserted provider tags into protected segment {segment['segment_id']}.",
        )

    if provider == "cartesia":
        if case["prosody_cue_counts"].get("pause", 0) > 0:
            assert_condition(
                variant["mapped_cue_counts"]["pause"] > 0,
                f"{case['case_id']} Cartesia should map pause cues when present.",
            )
        if case["prosody_cue_counts"].get("rate", 0) > 0:
            assert_condition("<speed ratio=" in variant["rendered_text"], f"{case['case_id']} Cartesia missing speed tag.")
        if case["prosody_cue_counts"].get("emphasis", 0) > 0:
            assert_condition("<volume ratio=" in variant["rendered_text"], f"{case['case_id']} Cartesia missing volume emphasis tag.")
        if case["prosody_cue_counts"].get("pause", 0) > 0:
            assert_condition("<break time=\"" in variant["rendered_text"], f"{case['case_id']} Cartesia missing break tag.")

    if provider == "elevenlabs":
        if case["prosody_cue_counts"].get("pause", 0) > 0:
            assert_condition("<break time=\"" in variant["rendered_text"], f"{case['case_id']} ElevenLabs missing break tag.")
        assert_condition("<speed ratio=" not in variant["rendered_text"], f"{case['case_id']} ElevenLabs should not use Cartesia speed tags.")
        assert_condition("<volume ratio=" not in variant["rendered_text"], f"{case['case_id']} ElevenLabs should not use Cartesia volume tags.")
        assert_condition(0.9 <= variant["voice_settings"]["speed"] <= 1.08, f"{case['case_id']} ElevenLabs speed out of range.")


def main() -> None:
    assert_condition(RUNNER.exists(), "VOICE-016 runner is missing.")
    assert_condition(CASES_PATH.exists(), "VOICE-016 case file is missing.")
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
    assert_condition(TMP_JSON.exists(), "VOICE-016 validation JSON was not created.")
    assert_condition(TMP_REPORT.exists(), "VOICE-016 validation report was not created.")

    payload = json.loads(TMP_JSON.read_text(encoding="utf-8"))
    summary = payload["summary"]
    assert_condition(summary["case_count"] == 8, summary)
    assert_condition(summary["provider_count"] == 2, summary)
    assert_condition(summary["provider_calls_made"] is False, summary)
    assert_condition(summary["requires_api_key"] is False, summary)
    assert_condition(summary["customer_audio_uploaded"] is False, summary)
    assert_condition(summary["voice_cloning_used"] is False, summary)
    assert_condition(summary["validation_failed"] == 0, summary)
    assert_condition(summary["protected_segment_provider_tag_count"] == 0, summary)
    assert_condition(summary["provider_mapped_cue_counts"]["cartesia"]["pause"] >= 5, summary)
    assert_condition(summary["provider_mapped_cue_counts"]["cartesia"]["rate"] >= 5, summary)
    assert_condition(summary["provider_mapped_cue_counts"]["cartesia"]["emphasis"] >= 5, summary)
    assert_condition(summary["provider_mapped_cue_counts"]["elevenlabs"]["pause"] >= 5, summary)
    assert_condition(summary["provider_mapped_cue_counts"]["elevenlabs"]["rate"] >= 5, summary)

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
    assert_condition(
        first_payload_text == TMP_JSON.read_text(encoding="utf-8"),
        "VOICE-016 output should be deterministic for the same VOICE-015 source artifact.",
    )

    payload = json.loads(TMP_JSON.read_text(encoding="utf-8"))
    for case in payload["cases"]:
        assert_condition(len(case["provider_variants"]) == 2, f"{case['case_id']} should have two provider variants.")
        for variant in case["provider_variants"]:
            validate_provider_variant(case, variant)

    output_text = json.dumps(payload, ensure_ascii=False) + TMP_REPORT.read_text(encoding="utf-8") + completed.stdout
    match = SECRET_PATTERN.search(output_text)
    if match is not None:
        raise AssertionError(f"Potential secret-like value found in VOICE-016 output: {match.group(0)!r}")
    print("VOICE-016 provider prosody rendering validation passed.")


if __name__ == "__main__":
    main()
