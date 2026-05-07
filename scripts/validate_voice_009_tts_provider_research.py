#!/usr/bin/env python3
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "evaluate_voice_009_tts_provider_research.py"
CANDIDATES_PATH = ROOT / "research" / "experiments" / "cases" / "voice-009-tts-provider-research.json"
GENERATED_DIR = ROOT / ".tmp" / "VOICE-009"
OUT_JSON = GENERATED_DIR / "VOICE-009-tts-provider-research.json"
REPORT_OUT = GENERATED_DIR / "VOICE-009-tts-provider-research-report.md"


SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|OPENAI_API_KEY\s*=\s*[^\s]+|Authorization:\s*Bearer\s+[A-Za-z0-9])"
)

OFFICIAL_HOST_SUFFIXES = {
    "docs.cartesia.ai",
    "cartesia.ai",
    "elevenlabs.io",
    "platform.openai.com",
    "developers.openai.com",
    "learn.microsoft.com",
    "azure.microsoft.com",
    "cloud.google.com",
    "docs.cloud.google.com",
    "docs.aws.amazon.com",
    "aws.amazon.com",
    "developers.deepgram.com",
    "deepgram.com",
    "github.com",
}


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_no_secret_patterns(text: str) -> None:
    match = SECRET_PATTERN.search(text)
    if match is not None:
        raise AssertionError(f"Potential secret-like token found: {match.group(0)!r}")


def is_official_url(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return host in OFFICIAL_HOST_SUFFIXES or any(host.endswith(f".{suffix}") for suffix in OFFICIAL_HOST_SUFFIXES)


def run_research() -> dict:
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
    assert_condition(SCRIPT_PATH.exists(), "VOICE-009 TTS provider research evaluator is missing.")
    assert_condition(CANDIDATES_PATH.exists(), "VOICE-009 TTS provider research file is missing.")

    result = run_research()
    assert_condition(result["voice_milestone"] == "VOICE-009", "Unexpected milestone.")
    assert_condition(result["summary"]["api_calls_made"] is False, "VOICE-009 must not make API calls.")
    assert_condition(result["summary"]["audio_uploaded"] is False, "VOICE-009 must not upload audio.")
    assert_condition(result["summary"]["secrets_required"] is False, "VOICE-009 must not require secrets.")
    assert_condition(result["summary"]["candidate_count"] >= 8, "Expected at least eight TTS provider candidates.")
    assert_condition(result["summary"]["source_count"] >= 8, "Expected at least eight official/primary sources.")
    assert_condition(result["summary"]["official_source_count"] == result["summary"]["source_count"], "All sources must be official/primary.")
    assert_condition({"de", "en"}.issubset(set(result["summary"]["languages_evaluated"])), "German and English must be evaluated.")
    assert_condition(result["summary"]["cloud_candidates_key_gated"] >= 6, "Cloud candidates should remain key-gated.")
    assert_condition(result["summary"]["voice_clone_candidates_blocked"] >= 2, "Voice cloning/custom voices must remain gated.")
    assert_condition(result["research_gate"]["retrieved_on"] == "2026-05-01", "Source retrieval date should be explicit.")
    assert_condition(result["research_gate"]["api_key_storage_rule"] == "environment-only-not-repo", "API keys must stay out of repo.")
    assert_condition(result["research_gate"]["integration_allowed"] is False, "VOICE-009 is research only, not integration.")

    recommendations = result["recommendations"]
    assert_condition(
        recommendations["recommended_first_integration"]["provider_id"] == "cartesia-sonic-3",
        "Cartesia Sonic 3 should be the first TTS integration candidate.",
    )
    assert_condition(
        recommendations["quality_alternate"]["provider_id"] == "elevenlabs-flash-v2-5",
        "ElevenLabs Flash v2.5 should be the quality/latency alternate.",
    )
    assert_condition(
        recommendations["stack_simplest_alternate"]["provider_id"] == "openai-gpt-4o-mini-tts",
        "OpenAI TTS should be the stack-simplest alternate.",
    )
    assert_condition(
        recommendations["enterprise_alternate"]["provider_id"] in {"google-cloud-chirp-3-hd", "azure-ai-speech-neural"},
        "Enterprise alternate should be Google or Azure.",
    )
    assert_condition(
        recommendations["do_not_integrate_first"]["provider_id"] == "deepgram-aura-2",
        "Deepgram Aura should not be recommended first while German TTS support is missing.",
    )
    assert_condition(
        recommendations["offline_research_lane"]["provider_id"] == "piper-local-tts",
        "Piper should remain the offline research lane.",
    )

    source_ids = {source["source_id"] for source in result["sources"]}
    for source in result["sources"]:
        assert_condition(source["retrieved_on"] == "2026-05-01", f"{source['source_id']} missing retrieval date.")
        assert_condition(is_official_url(source["url"]), f"{source['source_id']} is not official/primary: {source['url']}")

    required_ids = {
        "cartesia-sonic-3",
        "elevenlabs-flash-v2-5",
        "openai-gpt-4o-mini-tts",
        "azure-ai-speech-neural",
        "google-cloud-chirp-3-hd",
        "amazon-polly-neural",
        "deepgram-aura-2",
        "piper-local-tts",
    }
    candidates = result["ranked_candidates"]
    provider_ids = {candidate["provider_id"] for candidate in candidates}
    assert_condition(required_ids.issubset(provider_ids), f"Missing provider candidates: {sorted(required_ids - provider_ids)}")

    for candidate in candidates:
        assert_condition(candidate["official_sources"], f"{candidate['provider_id']} must cite official sources.")
        assert_condition(set(candidate["official_sources"]).issubset(source_ids), f"{candidate['provider_id']} cites unknown source IDs.")
        assert_condition(candidate["audio_uploaded"] is False, f"{candidate['provider_id']} should not upload audio in VOICE-009.")
        assert_condition(candidate["api_calls_made"] is False, f"{candidate['provider_id']} should not call APIs in VOICE-009.")
        if candidate["requires_api_key"]:
            assert_condition(candidate["key_gate"] == "required-before-integration", f"{candidate['provider_id']} must be key-gated.")
            assert_condition(candidate["launch_allowed"] is False, f"{candidate['provider_id']} should not launch before key/privacy review.")
        if candidate["voice_cloning_available"] or candidate["custom_voice_available"]:
            assert_condition(candidate["voice_clone_allowed_for_first_integration"] is False, f"{candidate['provider_id']} voice cloning must stay blocked.")
            assert_condition(candidate["consent_legal_gate"] == "required-before-any-custom-or-cloned-voice", f"{candidate['provider_id']} needs consent/legal gate.")
        if candidate["provider_id"] == "deepgram-aura-2":
            assert_condition("de" not in candidate["language_support"], "Deepgram Aura should not claim German support unless official docs confirm it.")
            assert_condition("missing-german-tts-support" in candidate["blockers"], "Deepgram should be blocked by German support gap.")
        if candidate["recommended_role"] in {"recommended-first-integration", "quality-alternate", "stack-simplest-alternate", "enterprise-alternate"}:
            assert_condition({"de", "en"}.issubset(set(candidate["language_support"])), f"{candidate['provider_id']} needs German and English support.")

    assert_condition(OUT_JSON.exists(), "Expected VOICE-009 JSON artifact.")
    assert_condition(REPORT_OUT.exists(), "Expected VOICE-009 Markdown report artifact.")
    report_text = REPORT_OUT.read_text(encoding="utf-8")
    assert_condition("No API calls were made" in report_text, "Report should state no API calls.")
    assert_condition("No audio was uploaded" in report_text, "Report should state no audio upload.")
    assert_condition("German and English" in report_text, "Report should mention German and English.")
    assert_condition("retrieved on 2026-05-01" in report_text, "Report should include source retrieval date.")
    assert_condition("recommended first integration" in report_text.lower(), "Report should include the first integration recommendation.")
    assert_condition("Cartesia" in report_text, "Report should discuss Cartesia.")
    assert_condition("ElevenLabs" in report_text, "Report should discuss ElevenLabs.")
    assert_condition("OpenAI" in report_text, "Report should discuss OpenAI.")
    assert_condition("Deepgram" in report_text, "Report should discuss Deepgram limitation.")

    serialized = json.dumps(result) + report_text
    assert_no_secret_patterns(serialized)
    print("VOICE-009 TTS provider research validation passed.")


if __name__ == "__main__":
    main()
