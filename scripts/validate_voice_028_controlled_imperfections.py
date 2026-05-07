#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from speech_imperfections import apply_speech_imperfections  # noqa: E402

RUNNER_PATH = ROOT / "scripts" / "run_voice_028_controlled_imperfections.py"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "voice-028-controlled-imperfections.json"
RUN_DIR = ROOT / "research" / "experiments" / "generated" / "VOICE-028-controlled-imperfections"
RESULTS_PATH = RUN_DIR / "results.json"
REPORT_PATH = RUN_DIR / "report.md"


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=30)


def base_campaign(language: str) -> dict[str, Any]:
    return {
        "campaign_id": f"voice-028-{language}",
        "client_name": "Synthetic VOICE-028 Client",
        "product_name": "Controlled imperfections",
        "product_category": "generic-sales",
        "customer_type": "b2c",
        "language": language,
        "approved_opening": "Hello.",
        "qualification_questions": [
            "Can I ask one quick question first?",
            "Darf ich Ihnen zuerst eine kurze Frage stellen?",
        ],
        "required_disclosures": [
            "This is a test disclosure.",
            "Dies ist ein Testhinweis.",
        ],
        "speech_imperfections": {
            "enabled": True,
            "style": "professional-human",
            "max_imperfections_per_response": 1,
            "allow_clarifying_rephrases": True,
            "allow_breath_pauses": True,
            "allow_soft_restarts": True,
        },
    }


def single_segment(segment_id: str, text: str) -> list[dict[str, Any]]:
    return [
        {
            "segment_id": segment_id,
            "segment_type": "freeform_explanation",
            "source": "agent_freeform",
            "text": text,
            "allow_speech_imperfections": True,
            "allow_prosody": True,
        }
    ]


def validate_freeform_imperfection(language: str) -> None:
    text = (
        "I can keep this simple. The useful thing is to check whether the next step is relevant before anyone spends more time on it."
        if language == "en"
        else "Ich halte es kurz. Wir klaeren nur, ob der naechste Schritt fuer Sie relevant ist, bevor jemand mehr Zeit investiert."
    )
    packet = apply_speech_imperfections(
        campaign=base_campaign(language),
        segments=single_segment(f"voice-028-{language}", text),
        language=language,
        seed=f"VOICE-028-{language}",
        customer_state={"emotion": "curious"},
    )
    assert_condition(packet["validation"]["passed"] is True, f"{language} imperfection packet should pass.")
    assert_condition(packet["imperfection_count"] == 1, f"{language} should add exactly one imperfection.")
    imperfection = packet["imperfections"][0]
    assert_condition(imperfection["visible"] is True, f"{language} freeform imperfection should be visible.")
    assert_condition(imperfection["imperfection_type"] in {"clarifying_rephrase", "soft_restart"}, imperfection)
    assert_condition(packet["tts_text"] != text, f"{language} tts text should change for eligible freeform.")
    if language == "en":
        assert_condition(
            re.search(r"\b(actually|i mean|more simply)\b", packet["tts_text"], re.IGNORECASE),
            packet["tts_text"],
        )
    else:
        assert_condition(
            re.search(r"\b(also|genauer gesagt|anders gesagt)\b", packet["tts_text"], re.IGNORECASE),
            packet["tts_text"],
        )


def validate_protected_question_stays_exact() -> None:
    protected_text = "Darf ich Ihnen zuerst eine kurze Frage stellen?"
    packet = apply_speech_imperfections(
        campaign=base_campaign("de"),
        segments=[
            {
                "segment_id": "voice-028-de-protected",
                "segment_type": "campaign_qualification_question",
                "source": "campaign_config",
                "text": protected_text,
            }
        ],
        language="de",
        seed="VOICE-028-DE-PROTECTED",
        customer_state={"emotion": "neutral"},
    )
    output = packet["output_segments"][0]
    assert_condition(output["text_after"] == protected_text, "Protected German question changed.")
    assert_condition(not output["imperfections"], "Protected German question received an imperfection.")
    assert_condition(packet["imperfection_count"] == 0, "Protected-only packet should not add imperfections.")


def validate_unsafe_context_suppresses_visible_imperfections() -> None:
    text = "I can explain the limits clearly. The useful thing is to compare fit without promising a result."
    packet = apply_speech_imperfections(
        campaign=base_campaign("en"),
        segments=single_segment("voice-028-en-unsafe", text),
        language="en",
        seed="VOICE-028-EN-UNSAFE",
        customer_state={"emotion": "skeptical", "unsafe_claim_present": True},
    )
    assert_condition(packet["validation"]["passed"] is True, "Unsafe packet should pass.")
    assert_condition(packet["imperfection_count"] == 0, "Unsafe claim context should not add visible imperfections.")
    assert_condition(packet["tts_text"] == text, "Unsafe claim text should stay exact.")


def validate_stop_intent_suppresses_imperfections() -> None:
    text = "I will stop the call here and respect that."
    packet = apply_speech_imperfections(
        campaign=base_campaign("en"),
        segments=single_segment("voice-028-en-stop", text),
        language="en",
        seed="VOICE-028-EN-STOP",
        customer_state={"emotion": "angry", "stop_intent": True},
    )
    assert_condition(packet["validation"]["passed"] is True, "Stop packet should pass.")
    assert_condition(packet["imperfection_count"] == 0, "Stop intent should suppress imperfections.")
    assert_condition(packet["tts_text"] == text, "Stop text should stay exact.")


def validate_runner_artifacts() -> None:
    assert_condition(RUNNER_PATH.exists(), "VOICE-028 runner is missing.")
    assert_condition(CASES_PATH.exists(), "VOICE-028 case file is missing.")
    completed = run_command(
        [
            sys.executable,
            str(RUNNER_PATH),
            "--cases",
            str(CASES_PATH),
            "--out",
            str(RESULTS_PATH),
            "--report-out",
            str(REPORT_PATH),
        ]
    )
    assert_condition(completed.returncode == 0, f"VOICE-028 runner failed: {completed.stderr or completed.stdout}")
    assert_condition(RESULTS_PATH.exists(), "VOICE-028 results were not created.")
    assert_condition(REPORT_PATH.exists(), "VOICE-028 report was not created.")

    payload = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    summary = payload["summary"]
    assert_condition(summary["case_count"] == 5, "VOICE-028 should cover five cases.")
    assert_condition(summary["languages"] == {"en": 3, "de": 2}, "VOICE-028 should cover English and German.")
    assert_condition(summary["validation_failed"] == 0, "VOICE-028 has failed validations.")
    assert_condition(summary["provider_calls_made"] is False, "VOICE-028 must be offline.")
    assert_condition(summary["customer_audio_uploaded"] is False, "VOICE-028 must not upload customer audio.")
    assert_condition(summary["voice_cloning_used"] is False, "VOICE-028 must not use voice cloning.")
    assert_condition(summary["protected_segment_change_count"] == 0, "VOICE-028 changed protected campaign text.")
    assert_condition(summary["unsafe_visible_imperfection_count"] == 0, "VOICE-028 added visible imperfections in unsafe contexts.")
    assert_condition(summary["imperfection_count"] == 2, "VOICE-028 should add imperfections only to the two safe freeform cases.")
    assert_condition("clarifying_rephrase" in summary["imperfection_types"], "Summary should include clarifying rephrases.")

    report_text = REPORT_PATH.read_text(encoding="utf-8")
    assert_condition("Controlled Imperfection Rule" in report_text, "VOICE-028 report should document the rule.")


def main() -> None:
    validate_freeform_imperfection("en")
    validate_freeform_imperfection("de")
    validate_protected_question_stays_exact()
    validate_unsafe_context_suppresses_visible_imperfections()
    validate_stop_intent_suppresses_imperfections()
    validate_runner_artifacts()
    print("VOICE-028 controlled imperfections validation passed.")


if __name__ == "__main__":
    main()
