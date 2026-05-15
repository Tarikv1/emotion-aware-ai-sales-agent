#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from runtime.voice.voice_baseline_delivery_polish import apply_voice_baseline_delivery_polish


RUNNER = ROOT / "scripts" / "run_voice_044_baseline_delivery_polish.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "voice-044-baseline-delivery-polish.json"
DOC_PATH = ROOT / "docs" / "product" / "VOICE_044_BASELINE_DELIVERY_POLISH.md"
TMP_DIR = ROOT / ".tmp" / "voice-044-baseline-delivery-polish-validation"
TMP_JSON = TMP_DIR / "result.json"
TMP_REPORT = TMP_DIR / "report.md"


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def base_provider_rendering(text: str, *, language: str = "en", protected: bool = False) -> dict[str, Any]:
    segment_type = "do_not_call" if protected else "freeform_objection_handling"
    return {
        "provider_rendering_id": "VOICE-016-provider-prosody-rendering",
        "provider_key": "elevenlabs",
        "provider_name": "ElevenLabs Flash v2.5",
        "provider_rendering_mode": "break_tags_and_request_settings",
        "model_id": "eleven_flash_v2_5",
        "language": language,
        "case_id": "voice-044-validation",
        "plain_text": text,
        "rendered_text": text,
        "rendered_text_html_preview": text,
        "voice_settings": {
            "stability": 0.56,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True,
            "speed": 1.0 if language == "en" else 0.995,
        },
        "segment_renderings": [
            {
                "segment_id": "resp-002-final-response",
                "segment_type": segment_type,
                "protected_reason": "policy_or_compliance_boundary" if protected else None,
                "eligible_for_prosody": not protected,
                "plain_text": text,
                "rendered_text": text,
                "provider_tags_inserted": [],
            }
        ],
        "provider_tag_count": text.count("<break"),
        "protected_segment_provider_tag_count": text.count("<break") if protected else 0,
        "api_call_made": False,
        "requires_api_key": False,
        "customer_audio_uploaded": False,
        "voice_cloning_used": False,
        "generated_audio_created": False,
    }


def validate_english_fast_filler_cleanup() -> None:
    source_text = "I'll keep this practical, so, you're right to ask. It only matters if the next step is useful."
    result = apply_voice_baseline_delivery_polish(
        {},
        base_provider_rendering(source_text),
        language="en",
        seed="voice-044-en",
    )
    polished = result["polished_provider_rendering"]
    assert_condition(result["voice_milestone"] == "VOICE-044", result)
    assert_condition(result["applied"] is True, result)
    assert_condition(result["adjustment_count"] == 1, result)
    assert_condition(", so, you're right to ask" not in polished["rendered_text"].lower(), polished["rendered_text"])
    assert_condition("I'll keep this practical. You're right to ask." in polished["rendered_text"], polished["rendered_text"])
    assert_condition(polished["voice_settings"]["style"] == 0.0, polished["voice_settings"])
    assert_condition(polished["voice_settings"]["speed"] == 1.0, polished["voice_settings"])
    assert_condition(result["validation"]["passed"] is True, result["validation"])
    assert_condition(result["runtime_boundary"]["provider_calls_made"] is False, result["runtime_boundary"])


def validate_german_connector_and_break_cleanup() -> None:
    source_text = "Ich hab verstanden. <break time=\"0.245s\" /> Also, Wenn's passt, gibt's einen kurzen naechsten Schritt."
    result = apply_voice_baseline_delivery_polish(
        {},
        base_provider_rendering(source_text, language="de"),
        language="de",
        seed="voice-044-de",
    )
    polished = result["polished_provider_rendering"]
    assert_condition(result["applied"] is True, result)
    assert_condition(result["adjustment_count"] == 2, result)
    assert_condition("<break time=\"0.18s\" />" in polished["rendered_text"], polished["rendered_text"])
    assert_condition("also wenn's passt" in polished["rendered_text"], polished["rendered_text"])
    assert_condition("Also, Wenn's" not in polished["rendered_text"], polished["rendered_text"])
    assert_condition(polished["voice_settings"]["speed"] == 0.995, polished["voice_settings"])
    assert_condition(polished["voice_settings"]["style"] == 0.0, polished["voice_settings"])
    assert_condition(result["validation"]["passed"] is True, result["validation"])


def validate_protected_segment_is_unchanged() -> None:
    source_text = "Please do not call again, so, you're right to ask."
    source = base_provider_rendering(source_text, protected=True)
    result = apply_voice_baseline_delivery_polish(
        {},
        source,
        language="en",
        seed="voice-044-protected",
    )
    assert_condition(result["applied"] is False, result)
    assert_condition(result["adjustment_count"] == 0, result)
    assert_condition(result["polished_provider_rendering"] == source, "Protected segment changed.")
    assert_condition(result["validation"]["passed"] is True, result["validation"])


def validate_runner_checkpoint() -> None:
    assert_condition(DOC_PATH.exists(), "VOICE-044 product doc is missing.")
    assert_condition(CASE_PATH.exists(), "VOICE-044 case file is missing.")
    assert_condition(RUNNER.exists(), "VOICE-044 runner is missing.")
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--out",
            str(TMP_JSON),
            "--report-out",
            str(TMP_REPORT),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    payload = json.loads(TMP_JSON.read_text(encoding="utf-8"))
    summary = payload["summary"]
    assert_condition(summary["case_count"] == 3, summary)
    assert_condition(summary["baseline_polish_applied_count"] == 2, summary)
    assert_condition(summary["private_pattern_profile_applied_count"] == 0, summary)
    assert_condition(summary["provider_calls_made"] is False, summary)
    assert_condition(summary["customer_audio_uploaded"] is False, summary)
    assert_condition(summary["voice_cloning_used"] is False, summary)
    assert_condition(summary["validation_passed"] is True, summary)
    for case in payload["cases"]:
        assert_condition(case["voice_private_pattern_profile"]["applied"] is False, case)
        assert_condition(case["validation"]["passed"] is True, case["validation"])


def main() -> None:
    validate_english_fast_filler_cleanup()
    validate_german_connector_and_break_cleanup()
    validate_protected_segment_is_unchanged()
    validate_runner_checkpoint()
    print("VOICE-044 baseline delivery polish validation passed.")


if __name__ == "__main__":
    main()
