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
    assert_condition(summary["case_count"] == 6, summary)
    assert_condition(summary["safe_case_count"] == 6, summary)
    assert_condition(summary["unsafe_case_count"] == 0, summary)
    assert_condition(summary["english_case_count"] == 3, summary)
    assert_condition(summary["german_case_count"] == 3, summary)
    assert_condition(summary["matched_pair_count"] == 3, summary)
    assert_condition(summary["both_languages_have_spoken_normalization"] is True, summary)
    assert_condition(summary["both_languages_have_prosody"] is True, summary)
    assert_condition(summary["both_languages_have_pacing"] is True, summary)
    assert_condition(summary["both_languages_have_emotion_smoothing"] is True, summary)

    by_pair: dict[str, set[str]] = {}
    for case in payload["cases"]:
        by_pair.setdefault(case["pair_id"], set()).add(case["language"])
        assert_condition(case["required_spoken_fragments_present"] is True, case)
        assert_condition(case["forbidden_spoken_fragments_absent"] is True, case)
        assert_condition(case["provider_rendering_changed"] is True, case)
        assert_condition(case["protected_segment_provider_tag_count"] == 0, case)
        assert_condition(case["spoken_normalization_count"] >= 1, case)
        assert_condition(case["prosody_cue_count"] >= 1, case)
        assert_condition(case["pacing_tuned_segment_count"] >= 1, case)
        assert_condition(case["emotion_smoothed_transition_count"] >= 1, case)
    assert_condition(by_pair == {"objection": {"de", "en"}, "trust": {"de", "en"}, "next_step": {"de", "en"}}, by_pair)

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
