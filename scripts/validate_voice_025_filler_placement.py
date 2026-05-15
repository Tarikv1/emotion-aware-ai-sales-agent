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


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from runtime.speech.speech_realism import apply_speech_realism  # noqa: E402

RUNNER_PATH = ROOT / "scripts" / "run_voice_025_filler_placement.py"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "voice-025-filler-placement.json"
RUN_DIR = ROOT / "research" / "experiments" / "generated" / "VOICE-025-filler-placement"
RESULTS_PATH = RUN_DIR / "results.json"
REPORT_PATH = RUN_DIR / "report.md"


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=30)


def base_campaign(language: str) -> dict[str, Any]:
    return {
        "campaign_id": f"voice-025-{language}",
        "client_name": "Synthetic VOICE-025 Client",
        "product_name": "Boundary-aware sales response",
        "product_category": "generic-sales",
        "customer_type": "b2c",
        "language": language,
        "approved_opening": "Hello.",
        "qualification_questions": [
            "Can I ask one short question?",
            "Darf ich Ihnen eine kurze Frage stellen?",
        ],
        "required_disclosures": [
            "This is a test disclosure.",
            "Das ist ein Testhinweis.",
        ],
        "speech_realism": {
            "enabled": True,
            "style": "professional-human",
            "filler_frequency": "low",
            "max_bundles_per_response": 1,
            "allow_thinking_fillers": True,
            "allow_empathy_acknowledgements": True,
        },
    }


def single_segment(segment_id: str, text: str) -> list[dict[str, Any]]:
    return [
        {
            "segment_id": segment_id,
            "segment_type": "freeform_objection_handling",
            "source": "agent_freeform",
            "text": text,
            "allow_speech_realism": True,
            "allow_fillers": True,
        }
    ]


def validate_english_boundary_placement() -> None:
    packet = apply_speech_realism(
        campaign=base_campaign("en"),
        segments=single_segment(
            "voice-025-en",
            "That's a fair concern. The important thing is that the next step only makes sense if it is practical.",
        ),
        language="en",
        seed="VOICE-025-EN",
    )
    text = packet["tts_text"]
    assert_condition(packet["validation"]["passed"] is True, "English packet should pass base validation.")
    assert_condition(packet["bundle_count"] == 1, "English boundary case should add one bundle.")
    assert_condition(
        not re.search(r"thing is,\s+(um|uh|hm|well|so),\s+that", text, re.IGNORECASE),
        f"English filler must not split 'the important thing is that': {text}",
    )
    assert_condition(
        re.search(r"concern\.\s+(Um|Uh|Well|So),\s+the important thing is that", text),
        f"English filler should move to the sentence boundary before the planning phrase: {text}",
    )
    strategy = packet["speech_bundles"][0].get("insertion_strategy")
    assert_condition(
        strategy == "pre_thinking_sentence",
        f"English filler should be marked as pre_thinking_sentence, got {strategy}",
    )


def validate_german_boundary_placement() -> None:
    packet = apply_speech_realism(
        campaign=base_campaign("de"),
        segments=single_segment(
            "voice-025-de",
            "Ich habe den Punkt verstanden. Wichtig ist, dass der naechste Schritt fuer Sie kurz und unverbindlich bleibt.",
        ),
        language="de",
        seed="VOICE-025-DE",
    )
    text = packet["tts_text"]
    assert_condition(packet["validation"]["passed"] is True, "German packet should pass base validation.")
    assert_condition(packet["bundle_count"] == 1, "German boundary case should add one bundle.")
    assert_condition(
        not re.search(r"Wichtig ist,\s+(also|ähm|äh|hm),\s+dass", text, re.IGNORECASE),
        f"German filler must not split 'Wichtig ist, dass': {text}",
    )
    assert_condition(
        re.search(r"verstanden\.\s+(Also|Ähm|Äh|Hm),\s+wichtig ist, dass", text),
        f"German filler should move to the sentence boundary before the planning phrase: {text}",
    )
    filler = packet["speech_bundles"][0].get("filler")
    assert_condition(filler in {"also", "ähm", "äh", "hm"}, f"German filler is not German-specific: {filler}")
    strategy = packet["speech_bundles"][0].get("insertion_strategy")
    assert_condition(
        strategy == "pre_thinking_sentence",
        f"German filler should be marked as pre_thinking_sentence, got {strategy}",
    )


def validate_protected_german_question_stays_exact() -> None:
    campaign = base_campaign("de")
    protected_text = "Darf ich Ihnen eine kurze Frage stellen?"
    packet = apply_speech_realism(
        campaign=campaign,
        segments=[
            {
                "segment_id": "voice-025-de-freeform",
                "segment_type": "freeform_empathy",
                "source": "agent_freeform",
                "text": "Ich verstehe den Einwand. Wichtig ist, dass wir nur den passenden naechsten Schritt klaeren.",
                "allow_speech_realism": True,
                "allow_fillers": True,
            },
            {
                "segment_id": "voice-025-de-question",
                "segment_type": "campaign_qualification_question",
                "source": "campaign_config",
                "text": protected_text,
            },
        ],
        language="de",
        seed="VOICE-025-DE-PROTECTED",
    )
    output_by_id = {segment["segment_id"]: segment for segment in packet["output_segments"]}
    protected_output = output_by_id["voice-025-de-question"]
    assert_condition(protected_output["text_after"] == protected_text, "Protected German question changed.")
    assert_condition(not protected_output["bundles"], "Protected German question received a filler bundle.")


def validate_german_sentence_boundary_fallback() -> None:
    packet = apply_speech_realism(
        campaign=base_campaign("de"),
        segments=single_segment(
            "voice-025-de-fallback",
            "Das verstehe ich gut. Wir halten es kurz und klaeren nur, ob ein Rueckruf fuer Sie sinnvoll ist.",
        ),
        language="de",
        seed="VOICE-025-DE-FALLBACK",
    )
    text = packet["tts_text"]
    assert_condition(packet["validation"]["passed"] is True, "German fallback packet should pass base validation.")
    assert_condition(
        re.search(r"gut\.\s+(Ähm|Also|Äh),\s+wir halten", text),
        f"German fallback should use a sentence-boundary marker and lowercase the resumed clause: {text}",
    )


def validate_runner_artifacts() -> None:
    assert_condition(RUNNER_PATH.exists(), "VOICE-025 runner is missing.")
    assert_condition(CASES_PATH.exists(), "VOICE-025 case file is missing.")
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
    assert_condition(completed.returncode == 0, f"VOICE-025 runner failed: {completed.stderr or completed.stdout}")
    assert_condition(RESULTS_PATH.exists(), "VOICE-025 results were not created.")
    assert_condition(REPORT_PATH.exists(), "VOICE-025 report was not created.")

    payload = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    assert_condition(payload["summary"]["case_count"] == 5, "VOICE-025 should cover five cases.")
    assert_condition(payload["summary"]["languages"] == {"en": 2, "de": 3}, "VOICE-025 should cover English and German.")
    assert_condition(payload["summary"]["validation_failed"] == 0, "VOICE-025 has failed validations.")
    assert_condition(payload["summary"]["provider_calls_made"] is False, "VOICE-025 must be offline.")
    assert_condition(payload["summary"]["customer_audio_uploaded"] is False, "VOICE-025 must not upload audio.")
    assert_condition(payload["summary"]["voice_cloning_used"] is False, "VOICE-025 must not use voice cloning.")
    assert_condition(
        payload["summary"]["protected_segment_change_count"] == 0,
        "VOICE-025 changed protected campaign text.",
    )
    for result in payload["results"]:
        tts_text = result["speech_realism"]["tts_text"]
        assert_condition(
            not re.search(r"thing is,\s+(um|uh|hm|well|so),\s+that", tts_text, re.IGNORECASE),
            f"{result['case_id']} contains old bad English placement: {tts_text}",
        )
        assert_condition(
            not re.search(r"Wichtig ist,\s+(also|ähm|äh|hm),\s+dass", tts_text, re.IGNORECASE),
            f"{result['case_id']} contains old bad German placement: {tts_text}",
        )

    report_text = REPORT_PATH.read_text(encoding="utf-8")
    assert_condition("Boundary Rule" in report_text, "VOICE-025 report should document the boundary rule.")


def main() -> None:
    validate_english_boundary_placement()
    validate_german_boundary_placement()
    validate_protected_german_question_stays_exact()
    validate_german_sentence_boundary_fallback()
    validate_runner_artifacts()
    print("VOICE-025 filler placement validation passed.")


if __name__ == "__main__":
    main()
