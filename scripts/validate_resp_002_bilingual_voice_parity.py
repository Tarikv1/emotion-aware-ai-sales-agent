#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_resp_002_bilingual_voice_parity.py"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "RESP-002-bilingual-voice-parity" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "RESP-002-bilingual-voice-parity" / "report.md"


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=60)


def parse_stdout_json(completed: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Expected JSON stdout, got: {completed.stdout!r}") from exc


def main() -> None:
    assert_condition(RUNNER.exists(), "RESP-002 bilingual voice parity runner is missing.")
    completed = run_command([sys.executable, str(RUNNER)])
    assert_condition(completed.returncode == 0, completed.stderr)
    payload = parse_stdout_json(completed)
    summary = payload["summary"]

    assert_condition(payload["experiment_id"] == "RESP-002-bilingual-voice-parity", payload)
    assert_condition(payload["provider_calls_made"] is False, payload)
    assert_condition(payload["customer_audio_uploaded"] is False, payload)
    assert_condition(payload["voice_cloning_used"] is False, payload)
    assert_condition(payload["generated_audio_created"] is False, payload)
    assert_condition(summary["case_count"] == 2, summary)
    assert_condition(summary["safe_case_count"] == 2, summary)
    assert_condition(summary["unsafe_case_count"] == 0, summary)
    assert_condition(summary["english_case_count"] == 1, summary)
    assert_condition(summary["german_case_count"] == 1, summary)
    assert_condition(summary["both_languages_have_spoken_normalization"] is True, summary)
    assert_condition(summary["both_languages_have_prosody"] is True, summary)
    assert_condition(summary["both_languages_have_pacing"] is True, summary)
    assert_condition(summary["both_languages_have_emotion_smoothing"] is True, summary)

    by_language = {case["language"]: case for case in payload["cases"]}
    assert_condition(set(by_language) == {"de", "en"}, by_language)
    german = by_language["de"]
    english = by_language["en"]
    assert_condition(german["required_spoken_fragments_present"] is True, german)
    assert_condition(german["forbidden_spoken_fragments_absent"] is True, german)
    assert_condition(english["required_spoken_fragments_present"] is True, english)
    assert_condition(english["forbidden_spoken_fragments_absent"] is True, english)
    assert_condition(german["provider_rendering_changed"] is True, german)
    assert_condition(english["provider_rendering_changed"] is True, english)
    assert_condition(german["protected_segment_provider_tag_count"] == 0, german)
    assert_condition(english["protected_segment_provider_tag_count"] == 0, english)

    serialized = json.dumps(payload, ensure_ascii=False).lower().replace("\\", "/")
    for forbidden in ("data/private", "data/private-restricted", "api_key", "source_excerpt"):
        assert_condition(forbidden not in serialized, f"Forbidden boundary text leaked: {forbidden}")
    for hidden_emotion_claim in ("you are angry", "you are anxious", "i can tell you feel"):
        assert_condition(hidden_emotion_claim not in serialized, f"Hidden emotion claim leaked: {hidden_emotion_claim}")

    assert_condition(RESULT_PATH.exists(), "Parity result was not written.")
    assert_condition(REPORT_PATH.exists(), "Parity report was not written.")
    report_text = REPORT_PATH.read_text(encoding="utf-8")
    assert_condition("English and German" in report_text, "Report should explain bilingual parity.")
    print("RESP-002 bilingual voice parity validation passed.")


if __name__ == "__main__":
    main()
