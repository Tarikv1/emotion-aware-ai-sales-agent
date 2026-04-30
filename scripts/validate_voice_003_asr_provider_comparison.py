#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "compare_asr_providers.py"
PROVIDERS_PATH = ROOT / "research" / "experiments" / "cases" / "voice-003-asr-provider-candidates.json"
OUT_JSON = ROOT / "research" / "experiments" / "generated" / "VOICE-003-asr-provider-comparison.json"
REPORT_OUT = ROOT / "research" / "experiments" / "generated" / "VOICE-003-asr-provider-comparison-report.md"


def run_comparison() -> dict:
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--providers",
            str(PROVIDERS_PATH),
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


def assert_no_secret_patterns(text: str) -> None:
    assert "sk-" not in text
    assert "OPENAI_API_KEY" not in text
    assert "Authorization: Bearer" not in text


def main() -> None:
    assert SCRIPT_PATH.exists(), "VOICE-003 ASR comparison script is missing"
    assert PROVIDERS_PATH.exists(), "VOICE-003 ASR provider candidate file is missing"

    result = run_comparison()
    assert result["voice_milestone"] == "VOICE-003"
    assert result["summary"]["candidate_count"] >= 5
    assert result["summary"]["api_calls_made"] is False
    assert result["summary"]["audio_uploaded"] is False

    provider_ids = {candidate["provider_id"] for candidate in result["ranked_candidates"]}
    assert "manual-transcript-baseline" in provider_ids
    assert "browser-speech-recognition-demo" in provider_ids
    assert "cloud-streaming-asr-class" in provider_ids

    next_prototype = result["recommendations"]["next_prototype"]
    assert next_prototype["provider_id"] == "browser-speech-recognition-demo"
    assert next_prototype["requires_api_key"] is False

    baseline = result["recommendations"]["regression_baseline"]
    assert baseline["provider_id"] == "manual-transcript-baseline"
    assert baseline["requires_api_key"] is False

    cloud_candidates = [
        candidate for candidate in result["ranked_candidates"]
        if candidate["provider_id"].startswith("cloud-")
    ]
    assert cloud_candidates
    for candidate in cloud_candidates:
        assert candidate["requires_api_key"] is True
        assert "explicit key" in " ".join(candidate["decision_notes"]).lower()

    assert OUT_JSON.exists()
    assert REPORT_OUT.exists()
    report_text = REPORT_OUT.read_text(encoding="utf-8")
    assert "No API calls were made" in report_text
    assert "adapter boundary" in report_text.lower()
    assert "browser-speech-recognition-demo" in report_text

    serialized = json.dumps(result) + report_text
    assert_no_secret_patterns(serialized)


if __name__ == "__main__":
    main()
