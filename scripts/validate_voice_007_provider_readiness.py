#!/usr/bin/env python3
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "evaluate_voice_provider_readiness.py"
CANDIDATES_PATH = ROOT / "research" / "experiments" / "cases" / "voice-007-provider-readiness-candidates.json"
GENERATED_DIR = ROOT / ".tmp" / "VOICE-007"
OUT_JSON = GENERATED_DIR / "VOICE-007-provider-readiness.json"
REPORT_OUT = GENERATED_DIR / "VOICE-007-provider-readiness-report.md"


SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|OPENAI_API_KEY\s*=\s*[^\s]+|Authorization:\s*Bearer\s+[A-Za-z0-9])"
)


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_no_secret_patterns(text: str) -> None:
    match = SECRET_PATTERN.search(text)
    if match is not None:
        raise AssertionError(f"Potential secret-like token found: {match.group(0)!r}")


def run_readiness() -> dict:
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--candidates",
            str(CANDIDATES_PATH),
            "--out",
            str(OUT_JSON),
            "--report-out",
            str(REPORT_OUT),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def main() -> None:
    assert_condition(SCRIPT_PATH.exists(), "VOICE-007 provider readiness script is missing.")
    assert_condition(CANDIDATES_PATH.exists(), "VOICE-007 provider readiness candidate file is missing.")

    result = run_readiness()
    assert_condition(result["voice_milestone"] == "VOICE-007", "Unexpected milestone.")
    assert_condition(result["summary"]["api_calls_made"] is False, "VOICE-007 must not make API calls.")
    assert_condition(result["summary"]["audio_uploaded"] is False, "VOICE-007 must not upload audio.")
    assert_condition(result["summary"]["secrets_required"] is False, "VOICE-007 must not require secrets.")
    assert_condition(result["summary"]["candidate_count"] >= 10, "Expected ASR and TTS readiness candidates.")
    assert_condition(result["summary"]["role_counts"]["asr"] >= 4, "Expected multiple ASR candidates.")
    assert_condition(result["summary"]["role_counts"]["tts"] >= 4, "Expected multiple TTS candidates.")
    assert_condition({"de", "en"}.issubset(set(result["summary"]["languages_evaluated"])), "German and English must be evaluated.")
    assert_condition(result["summary"]["cloud_candidates_blocked_until_review"] >= 3, "Cloud candidates should remain gated.")
    assert_condition(result["readiness_gate"]["first_response_target_ms"] == 2000, "First response target should remain 2s.")
    assert_condition(result["readiness_gate"]["tts_start_target_ms"] == 500, "TTS start target should remain 500ms.")
    assert_condition(result["readiness_gate"]["api_key_storage_rule"] == "environment-only-not-repo", "API keys must stay out of repo.")

    recommendations = result["recommendations"]
    assert_condition(recommendations["regression_baselines"]["asr"]["provider_id"] == "manual-transcript-baseline", "Unexpected ASR baseline.")
    assert_condition(recommendations["regression_baselines"]["tts"]["provider_id"] == "dry-run-tts-packet", "Unexpected TTS baseline.")
    assert_condition(recommendations["next_no_key_prototypes"]["asr"]["provider_id"] == "browser-speech-recognition-demo", "Unexpected no-key ASR prototype.")
    assert_condition(recommendations["next_no_key_prototypes"]["tts"]["provider_id"] == "windows-sapi-local-tts", "Unexpected no-key TTS prototype.")
    assert_condition(recommendations["production_followups"]["asr"]["provider_id"] == "cloud-streaming-asr-class", "Unexpected ASR production follow-up.")
    assert_condition(recommendations["production_followups"]["tts"]["provider_id"] == "cloud-low-latency-tts-class", "Unexpected TTS production follow-up.")

    candidates = result["ranked_candidates"]
    provider_ids = {candidate["provider_id"] for candidate in candidates}
    required_ids = {
        "manual-transcript-baseline",
        "browser-speech-recognition-demo",
        "local-offline-asr-class",
        "cloud-streaming-asr-class",
        "dry-run-tts-packet",
        "windows-sapi-local-tts",
        "browser-speech-synthesis-demo",
        "cloud-low-latency-tts-class",
        "cloud-voice-clone-tts-class",
    }
    assert_condition(required_ids.issubset(provider_ids), f"Missing provider candidates: {sorted(required_ids - provider_ids)}")

    for candidate in candidates:
        assert_condition({"de", "en"}.issubset(set(candidate["language_support"])), f"{candidate['provider_id']} must evaluate German and English.")
        if candidate["requires_api_key"]:
            assert_condition(candidate["key_gate"] == "required-before-integration", f"{candidate['provider_id']} must be key-gated.")
            assert_condition(candidate["launch_allowed"] is False, f"{candidate['provider_id']} should not be launch-allowed before key/privacy review.")
        if candidate["uploads_customer_audio"]:
            assert_condition(
                candidate["customer_audio_upload_gate"] == "blocked-until-privacy-review",
                f"{candidate['provider_id']} must gate customer-audio upload.",
            )
            assert_condition(candidate["consent_required"] is True, f"{candidate['provider_id']} must require consent for audio upload.")
            assert_condition(candidate["retention_review_required"] is True, f"{candidate['provider_id']} must require retention review.")
        if candidate["provider_id"] == "cloud-voice-clone-tts-class":
            blockers = set(candidate["blockers"])
            assert_condition("voice-consent" in blockers, "Voice cloning must require explicit voice consent.")
            assert_condition("legal-review" in blockers, "Voice cloning must require legal review.")
            assert_condition(candidate["recommended_next_action"] == "do-not-integrate-yet", "Voice cloning should stay blocked.")

    assert_condition(OUT_JSON.exists(), "Expected VOICE-007 JSON artifact.")
    assert_condition(REPORT_OUT.exists(), "Expected VOICE-007 Markdown report artifact.")
    report_text = REPORT_OUT.read_text(encoding="utf-8")
    assert_condition("No API calls were made" in report_text, "Report should state no API calls.")
    assert_condition("No audio was uploaded" in report_text, "Report should state no audio upload.")
    assert_condition("environment-only-not-repo" in report_text, "Report should include key storage rule.")
    assert_condition("German and English" in report_text, "Report should mention German and English.")
    assert_condition("cloud-voice-clone-tts-class" in report_text, "Report should include voice-clone gating.")

    serialized = json.dumps(result) + report_text
    assert_no_secret_patterns(serialized)
    print("VOICE-007 provider readiness validation passed.")


if __name__ == "__main__":
    main()
