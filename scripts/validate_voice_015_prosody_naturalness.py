#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_voice_015_prosody_naturalness.py"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "voice-015-prosody-naturalness.json"
TMP_DIR = ROOT / ".tmp" / "voice-015-validation"
TMP_JSON = TMP_DIR / "VOICE-015-prosody-naturalness.json"
TMP_REPORT = TMP_DIR / "VOICE-015-prosody-naturalness-report.md"

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

ALLOWED_CUE_TYPES = {"pause", "rate", "emphasis", "pitch", "stretch"}


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True)


def validate_case(result: dict) -> None:
    packet = result["prosody_naturalness"]
    expected = result["expected"]
    cues = packet["prosody_plan"]
    protected_ids = set(expected.get("protected_segment_ids_unchanged", []))

    assert_condition(packet["validation"]["passed"] is True, f"{result['case_id']} failed packet validation.")
    assert_condition(
        expected["min_cues"] <= len(cues) <= expected["max_cues"],
        f"{result['case_id']} cue count {len(cues)} outside expected range {expected}.",
    )
    assert_condition(
        expected["min_pause_cues"] <= packet["cue_counts"].get("pause", 0),
        f"{result['case_id']} should include at least {expected['min_pause_cues']} pause cue(s).",
    )
    assert_condition(
        expected["min_pitch_cues"] <= packet["cue_counts"].get("pitch", 0),
        f"{result['case_id']} should include at least {expected['min_pitch_cues']} pitch cue(s).",
    )
    assert_condition(
        expected["min_rate_cues"] <= packet["cue_counts"].get("rate", 0),
        f"{result['case_id']} should include at least {expected['min_rate_cues']} rate cue(s).",
    )
    assert_condition(
        expected["min_emphasis_cues"] <= packet["cue_counts"].get("emphasis", 0),
        f"{result['case_id']} should include at least {expected['min_emphasis_cues']} emphasis cue(s).",
    )

    for segment in packet["output_segments"]:
        segment_id = segment["segment_id"]
        segment_type = segment["segment_type"]
        if segment_id in protected_ids or segment_type in PROTECTED_TYPES:
            assert_condition(
                segment["text_before"] == segment["tts_text"],
                f"{result['case_id']} changed protected text in {segment_id}.",
            )
            assert_condition(
                segment["debug_text"] == segment["text_before"],
                f"{result['case_id']} changed protected debug text in {segment_id}.",
            )
            assert_condition(
                segment["cue_count"] == 0,
                f"{result['case_id']} added cues to protected segment {segment_id}.",
            )

    for cue in cues:
        assert_condition(cue["type"] in ALLOWED_CUE_TYPES, f"Unexpected cue type: {cue}")
        assert_condition(
            cue["segment_type"] not in PROTECTED_TYPES,
            f"{result['case_id']} added cue to protected type: {cue}",
        )
        if cue["type"] == "pause":
            assert_condition(120 <= cue["duration_ms"] <= 420, f"Pause outside safe range: {cue}")
        if cue["type"] == "rate":
            assert_condition(0.9 <= cue["ratio"] <= 1.08, f"Rate ratio outside safe range: {cue}")
        if cue["type"] == "pitch":
            assert_condition(
                cue["direction"] in {"warm-soft", "slight-rise", "steady-low"},
                f"Unexpected pitch direction: {cue}",
            )
        if cue["type"] == "emphasis":
            assert_condition("**" in packet["debug_text"], f"Debug text should show emphasis markers for {cue}")
            assert_condition("**" not in packet["tts_text"], "Clean TTS text must not contain Markdown emphasis.")
        if cue["type"] == "stretch":
            assert_condition(cue["variant"].endswith("..."), f"Stretch cue should use bounded ellipsis variant: {cue}")


def main() -> None:
    assert_condition(RUNNER.exists(), "VOICE-015 runner is missing.")
    assert_condition(CASES_PATH.exists(), "VOICE-015 case file is missing.")
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
    assert_condition(TMP_JSON.exists(), "VOICE-015 validation JSON was not created.")
    assert_condition(TMP_REPORT.exists(), "VOICE-015 validation report was not created.")

    payload = json.loads(TMP_JSON.read_text(encoding="utf-8"))
    summary = payload["summary"]
    assert_condition(summary["case_count"] == 8, summary)
    assert_condition(summary["languages"]["de"] == 4, summary)
    assert_condition(summary["languages"]["en"] == 4, summary)
    assert_condition(summary["validation_failed"] == 0, summary)
    assert_condition(summary["provider_calls_made"] is False, summary)
    assert_condition(summary["requires_api_key"] is False, summary)
    assert_condition(summary["customer_audio_uploaded"] is False, summary)
    assert_condition(summary["voice_cloning_used"] is False, summary)
    assert_condition(summary["profile_styles"] == ["professional-human"], summary)
    assert_condition(summary["protected_segment_cue_count"] == 0, summary)
    assert_condition(summary["cue_counts"]["pause"] >= 5, summary)
    assert_condition(summary["cue_counts"]["pitch"] >= 4, summary)
    assert_condition(summary["cue_counts"]["rate"] >= 3, summary)
    assert_condition(summary["cue_counts"]["emphasis"] >= 3, summary)
    assert_condition(summary["cue_counts"]["stretch"] >= 1, summary)

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
        "VOICE-015 output should be deterministic for the same seeds.",
    )

    payload = json.loads(TMP_JSON.read_text(encoding="utf-8"))
    for result in payload["results"]:
        validate_case(result)

    output_text = json.dumps(payload, ensure_ascii=False) + TMP_REPORT.read_text(encoding="utf-8") + completed.stdout
    match = SECRET_PATTERN.search(output_text)
    if match is not None:
        raise AssertionError(f"Potential secret-like value found in VOICE-015 output: {match.group(0)!r}")
    print("VOICE-015 prosody naturalness validation passed.")


if __name__ == "__main__":
    main()
