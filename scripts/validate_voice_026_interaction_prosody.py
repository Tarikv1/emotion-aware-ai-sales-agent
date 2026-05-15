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
from runtime.speech.speech_interaction import apply_speech_interaction  # noqa: E402

RUNNER_PATH = ROOT / "scripts" / "run_voice_026_interaction_prosody.py"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "voice-026-interaction-prosody.json"
RUN_DIR = ROOT / "research" / "experiments" / "generated" / "VOICE-026-interaction-prosody"
RESULTS_PATH = RUN_DIR / "results.json"
REPORT_PATH = RUN_DIR / "report.md"
REQUIRED_RUBRIC_KEYS = {
    "naturalness",
    "trust",
    "confidence",
    "warmth",
    "pace",
    "interruption_safety",
    "sales_usefulness",
    "protected_text_safety",
}


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=30)


def base_campaign(language: str) -> dict[str, Any]:
    return {
        "campaign_id": f"voice-026-{language}",
        "client_name": "Synthetic VOICE-026 Client",
        "product_name": "Interaction prosody",
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
        "speech_interaction": {
            "enabled": True,
            "style": "professional-human",
            "max_markers_per_response": 2,
            "allow_backchannels": True,
            "allow_latency_acknowledgement": True,
            "allow_sales_pace_variation": True,
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
            "allow_interaction_prosody": True,
        }
    ]


def validate_lookup_acknowledgement(language: str) -> None:
    text = (
        "The next step is simple: we check whether the offer is relevant."
        if language == "en"
        else "Der naechste Schritt ist kurz: Wir klaeren nur, ob das Angebot relevant ist."
    )
    packet = apply_speech_interaction(
        campaign=base_campaign(language),
        segments=single_segment(f"voice-026-{language}-lookup", text),
        language=language,
        seed=f"VOICE-026-{language}-LOOKUP",
        customer_state={"emotion": "curious", "requires_lookup": True, "processing_expected_ms": 1600},
    )
    assert_condition(packet["validation"]["passed"] is True, f"{language} lookup packet should pass validation.")
    assert_condition(packet["marker_count"] >= 2, f"{language} lookup packet should add acknowledgement and pace markers.")
    marker_types = {marker["marker_type"] for marker in packet["interaction_markers"]}
    assert_condition("latency_acknowledgement" in marker_types, f"{language} lookup should add latency acknowledgement.")
    assert_condition("sales_pace_variation" in marker_types, f"{language} lookup should add sales pace variation.")
    assert_condition(
        REQUIRED_RUBRIC_KEYS.issubset(packet["evaluation_rubric"]),
        f"{language} packet is missing listening rubric keys.",
    )
    if language == "en":
        assert_condition(
            packet["tts_text"].startswith(("Let me check that.", "I can check that.")),
            packet["tts_text"],
        )
    else:
        assert_condition(
            packet["tts_text"].startswith(("Das pruefe ich kurz.", "Ich schaue kurz nach.")),
            packet["tts_text"],
        )


def validate_unsafe_agreement_guard(language: str) -> None:
    text = (
        "I can explain the limits clearly. The useful thing is to compare the fit without promising a result."
        if language == "en"
        else "Ich kann die Grenzen klar einordnen. Sinnvoll ist nur zu pruefen, ob ein Fachgespraech passt."
    )
    packet = apply_speech_interaction(
        campaign=base_campaign(language),
        segments=single_segment(f"voice-026-{language}-unsafe", text),
        language=language,
        seed=f"VOICE-026-{language}-UNSAFE",
        customer_state={"emotion": "skeptical", "unsafe_claim_present": True},
    )
    assert_condition(packet["validation"]["passed"] is True, f"{language} unsafe guard packet should pass validation.")
    marker_types = {marker["marker_type"] for marker in packet["interaction_markers"]}
    assert_condition("neutral_backchannel" in marker_types, f"{language} unsafe guard should use neutral backchannel.")
    forbidden = r"\b(yes|exactly|that's right)\b" if language == "en" else r"\b(ja|genau)\b"
    assert_condition(
        not re.search(forbidden, packet["tts_text"], re.IGNORECASE),
        f"{language} unsafe guard used an agreement marker: {packet['tts_text']}",
    )
    assert_condition(
        not packet["validation"]["unsafe_agreement_markers"],
        f"{language} unsafe guard reported unsafe agreement markers.",
    )


def validate_protected_question_stays_exact() -> None:
    protected_text = "Darf ich Ihnen zuerst eine kurze Frage stellen?"
    packet = apply_speech_interaction(
        campaign=base_campaign("de"),
        segments=[
            {
                "segment_id": "voice-026-de-protected",
                "segment_type": "campaign_qualification_question",
                "source": "campaign_config",
                "text": protected_text,
            }
        ],
        language="de",
        seed="VOICE-026-DE-PROTECTED",
        customer_state={"emotion": "neutral"},
    )
    output = packet["output_segments"][0]
    assert_condition(output["text_after"] == protected_text, "Protected German question changed.")
    assert_condition(not output["markers"], "Protected German question received interaction markers.")
    assert_condition(packet["marker_count"] == 0, "Protected-only packet should not add markers.")


def validate_stop_intent_suppresses_markers() -> None:
    packet = apply_speech_interaction(
        campaign=base_campaign("en"),
        segments=single_segment("voice-026-en-stop", "I will stop the call here and respect that."),
        language="en",
        seed="VOICE-026-EN-STOP",
        customer_state={"emotion": "angry", "stop_intent": True},
    )
    assert_condition(packet["validation"]["passed"] is True, "Stop packet should pass validation.")
    assert_condition(packet["marker_count"] == 0, "Stop intent should suppress interaction markers.")
    assert_condition(packet["tts_text"] == "I will stop the call here and respect that.", "Stop text should stay exact.")


def validate_runner_artifacts() -> None:
    assert_condition(RUNNER_PATH.exists(), "VOICE-026 runner is missing.")
    assert_condition(CASES_PATH.exists(), "VOICE-026 case file is missing.")
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
    assert_condition(completed.returncode == 0, f"VOICE-026 runner failed: {completed.stderr or completed.stdout}")
    assert_condition(RESULTS_PATH.exists(), "VOICE-026 results were not created.")
    assert_condition(REPORT_PATH.exists(), "VOICE-026 report was not created.")

    payload = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    summary = payload["summary"]
    assert_condition(summary["case_count"] == 6, "VOICE-026 should cover six cases.")
    assert_condition(summary["languages"] == {"en": 3, "de": 3}, "VOICE-026 should cover English and German evenly.")
    assert_condition(summary["validation_failed"] == 0, "VOICE-026 has failed validations.")
    assert_condition(summary["provider_calls_made"] is False, "VOICE-026 must be offline.")
    assert_condition(summary["customer_audio_uploaded"] is False, "VOICE-026 must not upload customer audio.")
    assert_condition(summary["voice_cloning_used"] is False, "VOICE-026 must not use voice cloning.")
    assert_condition(summary["protected_segment_change_count"] == 0, "VOICE-026 changed protected campaign text.")
    assert_condition("latency_acknowledgement" in summary["marker_types"], "Summary should include latency markers.")
    assert_condition("neutral_backchannel" in summary["marker_types"], "Summary should include neutral backchannels.")
    assert_condition("sales_pace_variation" in summary["marker_types"], "Summary should include sales pace variation.")
    assert_condition(
        REQUIRED_RUBRIC_KEYS.issubset(payload["evaluation_rubric"]),
        "VOICE-026 payload is missing listening rubric keys.",
    )

    for result in payload["results"]:
        packet = result["speech_interaction"]
        assert_condition(packet["validation"]["passed"] is True, f"{result['case_id']} failed packet validation.")
        assert_condition(
            not packet["validation"]["protected_segment_changes"],
            f"{result['case_id']} changed protected text.",
        )
        assert_condition(
            not packet["validation"]["unsafe_agreement_markers"],
            f"{result['case_id']} emitted unsafe agreement markers.",
        )

    report_text = REPORT_PATH.read_text(encoding="utf-8")
    assert_condition("Interaction Prosody Rule" in report_text, "VOICE-026 report should document the rule.")


def main() -> None:
    validate_lookup_acknowledgement("en")
    validate_lookup_acknowledgement("de")
    validate_unsafe_agreement_guard("en")
    validate_unsafe_agreement_guard("de")
    validate_protected_question_stays_exact()
    validate_stop_intent_suppresses_markers()
    validate_runner_artifacts()
    print("VOICE-026 interaction prosody validation passed.")


if __name__ == "__main__":
    main()
