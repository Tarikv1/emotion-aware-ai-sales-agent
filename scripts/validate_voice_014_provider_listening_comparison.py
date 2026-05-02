#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_voice_014_provider_listening_comparison.py"
CASES = ROOT / "research" / "experiments" / "cases" / "voice-014-provider-listening-comparison.json"
OUT = ROOT / ".tmp" / "VOICE-014-provider-listening-comparison.json"
REPORT = ROOT / ".tmp" / "VOICE-014-provider-listening-comparison-report.md"
HTML = ROOT / ".tmp" / "VOICE-014-provider-listening-comparison.html"

SECRET_PATTERN = re.compile(
    r"(sk_car_[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|ELEVENLABS_API_KEY\s*=\s*[^\s<>]+|CARTESIA_API_KEY\s*=\s*[^\s<>]+|OPENAI_API_KEY\s*=\s*[^\s<>]+|Authorization:\s*Bearer\s+[A-Za-z0-9]|X-API-Key\s*[:=]\s*[A-Za-z0-9]|xi-api-key\s*[:=]\s*[A-Za-z0-9])"
)


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    assert_condition(SCRIPT.exists(), "VOICE-014 comparison runner is missing.")
    assert_condition(CASES.exists(), "VOICE-014 case file is missing.")
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--cases",
            str(CASES),
            "--out",
            str(OUT),
            "--report-out",
            str(REPORT),
            "--html-out",
            str(HTML),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(OUT.read_text(encoding="utf-8"))
    summary = payload["summary"]
    assert_condition(summary["comparison_count"] == 4, summary)
    assert_condition(summary["languages"] == {"de": 2, "en": 2}, summary)
    assert_condition(summary["providers"] == ["cartesia", "elevenlabs"], summary)
    assert_condition(summary["complete_audio_pairs"] == 4, summary)
    assert_condition(summary["provider_audio_counts"] == {"cartesia": 4, "elevenlabs": 4}, summary)
    assert_condition(summary["provider_calls_made"] is False, summary)
    assert_condition(summary["requires_api_key"] is False, summary)
    assert_condition(summary["customer_audio_uploaded"] is False, summary)
    assert_condition(summary["voice_cloning_used"] is False, summary)
    assert_condition(summary["human_ratings_recorded"] is False, summary)
    assert_condition(summary["quality_claim_allowed"] is False, summary)

    for comparison in payload["comparisons"]:
        assert_condition(len(comparison["providers"]) == 2, f"{comparison['comparison_id']} should have two providers.")
        providers = {provider["provider_key"]: provider for provider in comparison["providers"]}
        assert_condition(set(providers) == {"cartesia", "elevenlabs"}, comparison["providers"])
        assert_condition(providers["cartesia"]["audio_exists"] is True, f"{comparison['comparison_id']} missing Cartesia audio.")
        assert_condition(providers["elevenlabs"]["audio_exists"] is True, f"{comparison['comparison_id']} missing ElevenLabs audio.")
        assert_condition(providers["cartesia"]["first_audio_ms"] is not None, f"{comparison['comparison_id']} missing Cartesia first audio.")
        assert_condition(providers["elevenlabs"]["first_audio_ms"] is not None, f"{comparison['comparison_id']} missing ElevenLabs first audio.")
        assert_condition(
            comparison["human_rating_template"]["preferred_provider"] is None,
            f"{comparison['comparison_id']} should not preselect a provider.",
        )

    report_text = REPORT.read_text(encoding="utf-8")
    html_text = HTML.read_text(encoding="utf-8")
    assert_condition("No provider calls were made" in report_text, "Report should state no provider calls.")
    assert_condition("VOICE-014 Provider Listening Comparison" in report_text, "Report title missing.")
    assert_condition("<audio controls" in html_text, "HTML listening page should include audio controls.")
    assert_condition("VOICE-014" in html_text, "HTML should identify VOICE-014.")
    combined = completed.stdout + json.dumps(payload, ensure_ascii=False) + report_text + html_text
    match = SECRET_PATTERN.search(combined)
    if match is not None:
        raise AssertionError(f"Potential secret-like token found: {match.group(0)!r}")
    print("VOICE-014 provider listening comparison validation passed.")


if __name__ == "__main__":
    main()
