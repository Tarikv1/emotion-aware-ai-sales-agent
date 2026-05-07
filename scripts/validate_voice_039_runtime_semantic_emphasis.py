#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_voice_039_runtime_semantic_emphasis.py"
MODULE = ROOT / "scripts" / "voice_semantic_emphasis.py"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "voice-039-runtime-semantic-emphasis.json"
TMP_DIR = ROOT / ".tmp" / "voice-039-validation"
RESULT_PATH = TMP_DIR / "VOICE-039-runtime-semantic-emphasis-result.json"
REPORT_PATH = TMP_DIR / "VOICE-039-runtime-semantic-emphasis-report.md"
AUDIO_DIR = TMP_DIR / "audio"

SECRET_PATTERN = re.compile(
    r"(sk_car_[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|Authorization:\s*Bearer\s+[A-Za-z0-9]|X-API-Key\s*[:=]\s*[A-Za-z0-9]|xi-api-key\s*[:=]\s*[A-Za-z0-9])"
)

FRAGILE_PHRASE = "The practical next step is to check whether reviewing options is worth your time"
CLEAR_PHRASE = "We can quickly check if a review is worth your time"


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_no_secret_text(text: str, label: str) -> None:
    match = SECRET_PATTERN.search(text)
    if match is not None:
        raise AssertionError(f"Potential secret-like value found in {label}: {match.group(0)!r}")


def make_provider_rendering(
    text: str,
    *,
    language: str = "en",
    segment_type: str = "freeform_objection_handling",
    protected_reason: str | None = None,
    eligible_for_prosody: bool = True,
) -> dict:
    return {
        "provider_rendering_id": "test-provider-rendering",
        "provider_key": "elevenlabs",
        "provider_name": "ElevenLabs",
        "provider_rendering_mode": "break_tags_and_request_settings",
        "model_id": "eleven_flash_v2_5",
        "language": language,
        "case_id": "test-case",
        "plain_text": text,
        "rendered_text": text,
        "rendered_text_html_preview": text,
        "voice_settings": {"speed": 1.04, "stability": 0.56, "style": 0.12},
        "segment_renderings": [
            {
                "segment_id": "test-segment",
                "segment_type": segment_type,
                "protected_reason": protected_reason,
                "eligible_for_prosody": eligible_for_prosody,
                "plain_text": text,
                "rendered_text": text,
                "provider_tags_inserted": [],
                "mapped_cues": [],
                "unsupported_cues": [],
            }
        ],
        "mapped_cues": [],
        "unsupported_cues": [],
        "mapped_cue_counts": {"emphasis": 0, "pause": 0, "pitch": 0, "rate": 0, "stretch": 0},
        "unsupported_cue_counts": {"emphasis": 0, "pause": 0, "pitch": 0, "rate": 0, "stretch": 0},
        "provider_tag_count": 0,
        "protected_segment_provider_tag_count": 0,
        "api_call_made": False,
        "requires_api_key": False,
        "customer_audio_uploaded": False,
        "voice_cloning_used": False,
        "generated_audio_created": False,
    }


def validate_module_behavior() -> None:
    assert_condition(MODULE.exists(), "VOICE-039 semantic emphasis module is missing.")
    sys.path.insert(0, str(ROOT / "scripts"))
    from voice_semantic_emphasis import apply_voice_semantic_emphasis  # noqa: PLC0415

    source_text = (
        f"That makes sense. You do not need to change anything today. {FRAGILE_PHRASE}, "
        "and if it is not useful, we leave it there."
    )
    source_rendering = make_provider_rendering(source_text)
    result = apply_voice_semantic_emphasis({}, source_rendering, language="en")
    promoted = result["semantic_provider_rendering"]
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["rewrite_count"] == 1, result)
    assert_condition(result["eligible_segment_count"] == 1, result)
    assert_condition(CLEAR_PHRASE in promoted["rendered_text"], promoted["rendered_text"])
    assert_condition(FRAGILE_PHRASE not in promoted["rendered_text"], promoted["rendered_text"])
    assert_condition(source_rendering["rendered_text"] == source_text, "VOICE-039 must not mutate source rendering.")
    assert_condition(promoted["plain_text"] == source_text, "VOICE-039 must preserve the clean plain text audit trail.")
    assert_condition(promoted["api_call_made"] is False, promoted)
    assert_condition(promoted["customer_audio_uploaded"] is False, promoted)
    assert_condition(promoted["voice_cloning_used"] is False, promoted)

    protected = make_provider_rendering(
        source_text,
        segment_type="required_disclosure",
        protected_reason="policy_or_compliance_boundary",
        eligible_for_prosody=False,
    )
    protected_result = apply_voice_semantic_emphasis({}, protected, language="en")
    assert_condition(protected_result["rewrite_count"] == 0, protected_result)
    assert_condition(protected_result["semantic_provider_rendering"]["rendered_text"] == source_text, protected_result)
    assert_condition(protected_result["validation"]["protected_segment_text_changes"] == [], protected_result["validation"])
    assert_condition(protected_result["validation"]["passed"] is True, protected_result["validation"])

    german = make_provider_rendering(source_text, language="de")
    german_result = apply_voice_semantic_emphasis({}, german, language="de")
    assert_condition(german_result["rewrite_count"] == 0, german_result)
    assert_condition(german_result["semantic_provider_rendering"]["rendered_text"] == source_text, german_result)
    assert_condition(german_result["validation"]["passed"] is True, german_result["validation"])


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True)


def parse_stdout_json(completed: subprocess.CompletedProcess[str]) -> dict:
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Expected JSON stdout, got: {completed.stdout!r}") from exc


def validate_runner_payload(payload: dict) -> None:
    assert_condition(payload["voice_semantic_emphasis_runtime_id"] == "VOICE-039-runtime-semantic-emphasis", payload)
    summary = payload["summary"]
    assert_condition(summary["case_count"] == 3, summary)
    assert_condition(summary["provider_calls_made"] is False, summary)
    assert_condition(summary["audio_files_created"] == 0, summary)
    assert_condition(summary["semantic_rewrite_count"] == 1, summary)
    assert_condition(summary["protected_rewrite_count"] == 0, summary)
    assert_condition(summary["final_response_change_count"] == 0, summary)
    assert_condition(summary["validation_passed"] is True, summary)

    candidate = next(
        item for item in payload["results"] if item["case_id"] == "voice-039-en-long-clear-simple-runtime-candidate"
    )
    assert_condition(candidate["voice_semantic_emphasis"]["rewrite_count"] == 1, candidate)
    assert_condition(candidate["tts_delivery"]["tts_input_source"] == "provider_rendered_text", candidate)
    assert_condition(candidate["tts_delivery"]["provider_rendering_used"] is True, candidate)
    assert_condition(candidate["tts_delivery"]["provider_calls_made"] is False, candidate)
    assert_condition(candidate["tts_delivery"]["audio_file_created"] is False, candidate)
    assert_condition(candidate["long_script_tts_chars"] >= 180, candidate)
    assert_condition(FRAGILE_PHRASE in candidate["final_response"], candidate["final_response"])
    tts_text_lower = candidate["tts_delivery"]["tts_input_text"].lower()
    assert_condition(CLEAR_PHRASE.lower() in tts_text_lower, candidate["tts_delivery"]["tts_input_text"])
    assert_condition(FRAGILE_PHRASE.lower() not in tts_text_lower, candidate["tts_delivery"]["tts_input_text"])

    protected = next(item for item in payload["results"] if item["case_id"] == "voice-039-protected-do-not-call-lock")
    assert_condition(protected["voice_semantic_emphasis"]["rewrite_count"] == 0, protected)
    assert_condition(protected["tts_delivery"]["tts_input_source"] == "final_response", protected)
    assert_condition(protected["tts_delivery"]["provider_rendering_used"] is False, protected)

    german = next(item for item in payload["results"] if item["case_id"] == "voice-039-de-language-lock")
    assert_condition(german["voice_semantic_emphasis"]["rewrite_count"] == 0, german)
    assert_condition(german["voice_semantic_emphasis"]["language"] == "de", german)


def validate_forced_missing_live_fallback() -> None:
    forced_result = TMP_DIR / "VOICE-039-forced-missing-key-result.json"
    forced_report = TMP_DIR / "VOICE-039-forced-missing-key-report.md"
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--cases",
            str(CASES_PATH),
            "--provider",
            "elevenlabs",
            "--limit-cases",
            "1",
            "--live",
            "--force-key-missing",
            "--audio-dir",
            str(AUDIO_DIR),
            "--out",
            str(forced_result),
            "--report-out",
            str(forced_report),
        ]
    )
    assert_condition(completed.returncode == 0, completed.stderr)
    payload = parse_stdout_json(completed)
    assert_condition(payload["summary"]["live_call_requested"] is True, payload["summary"])
    assert_condition(payload["summary"]["provider_calls_made"] is False, payload["summary"])
    assert_condition(payload["summary"]["audio_files_created"] == 0, payload["summary"])
    assert_condition(payload["results"][0]["tts_delivery"]["fallback_reason"] == "forced-key-missing", payload["results"][0])


def validate_runner_behavior() -> None:
    assert_condition(RUNNER.exists(), "VOICE-039 runtime semantic emphasis runner is missing.")
    assert_condition(CASES_PATH.exists(), "VOICE-039 case file is missing.")
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--cases",
            str(CASES_PATH),
            "--provider",
            "elevenlabs",
            "--audio-dir",
            str(AUDIO_DIR),
            "--out",
            str(RESULT_PATH),
            "--report-out",
            str(REPORT_PATH),
        ]
    )
    assert_condition(completed.returncode == 0, completed.stderr)
    payload = parse_stdout_json(completed)
    validate_runner_payload(payload)
    assert_condition(RESULT_PATH.exists(), "VOICE-039 JSON result file was not created.")
    assert_condition(REPORT_PATH.exists(), "VOICE-039 Markdown report was not created.")
    validate_forced_missing_live_fallback()
    assert_no_secret_text(
        RESULT_PATH.read_text(encoding="utf-8")
        + REPORT_PATH.read_text(encoding="utf-8")
        + json.dumps(payload, ensure_ascii=False),
        "VOICE-039 artifacts",
    )


def main() -> None:
    validate_module_behavior()
    validate_runner_behavior()
    print("VOICE-039 runtime semantic emphasis validation passed.")


if __name__ == "__main__":
    main()
