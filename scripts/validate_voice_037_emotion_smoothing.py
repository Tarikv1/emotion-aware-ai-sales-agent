#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "voice_emotion_smoothing.py"
RUNNER = ROOT / "scripts" / "run_voice_037_emotion_smoothing.py"
RUNTIME_TTS_RUNNER = ROOT / "scripts" / "generate_runtime_tts_delivery.py"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "prod-005-realtime-latency-call-control.json"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "voice-037-emotion-smoothing.json"
DOC_PATH = ROOT / "docs" / "product" / "VOICE_037_EMOTION_TRANSITION_SMOOTHING.md"
TMP_DIR = ROOT / ".tmp" / "voice-037-validation"
VOICE_037_OUT_DIR = TMP_DIR / "runner"


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=30)


def parse_stdout_json(completed: subprocess.CompletedProcess[str]) -> dict:
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Expected JSON stdout, got {completed.stdout!r}") from exc


def load_module():
    spec = importlib.util.spec_from_file_location("voice_emotion_smoothing", MODULE)
    assert_condition(spec is not None and spec.loader is not None, "Could not load VOICE-037 module spec.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_resp_003(
    *,
    campaign: str,
    transcript: str,
    candidate_response: str | None = None,
    out_name: str,
) -> dict:
    args = [
        sys.executable,
        str(RUNTIME_TTS_RUNNER),
        "--campaign",
        campaign,
        "--stage",
        "relevance-check",
        "--transcript",
        transcript,
        "--cases",
        str(CASES_PATH),
        "--provider",
        "elevenlabs",
        "--audio-dir",
        str(TMP_DIR / "audio"),
        "--out",
        str(TMP_DIR / f"{out_name}.json"),
        "--report-out",
        str(TMP_DIR / f"{out_name}.md"),
    ]
    if candidate_response:
        args.extend(["--candidate-response", candidate_response])
    completed = run_command(args)
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    return parse_stdout_json(completed)


def validate_required_files() -> None:
    for path in [MODULE, RUNNER, CASE_PATH, DOC_PATH]:
        assert_condition(path.exists(), f"Required VOICE-037 file is missing: {path.relative_to(ROOT)}")


def validate_english_runtime_smoothing() -> None:
    payload = run_resp_003(
        campaign="campaign-prod-005-b2b-software",
        transcript="That sounds expensive.",
        candidate_response=(
            "I will keep this simple. You are right to ask. It is only useful if there is a practical next step."
        ),
        out_name="en-runtime",
    )
    delivery = payload["voice_delivery"]
    smoothing = delivery["voice_emotion_smoothing"]
    provider = delivery["provider_rendering"]
    tts = payload["tts_delivery"]

    assert_condition(smoothing["voice_milestone"] == "VOICE-037", smoothing)
    assert_condition(smoothing["language"] == "en", smoothing)
    assert_condition(smoothing["validation"]["passed"] is True, smoothing["validation"])
    assert_condition(delivery["validation"]["voice_emotion_smoothing_passed"] is True, delivery["validation"])
    assert_condition(smoothing["transition_smoothing_applied"] is True, smoothing)
    assert_condition(smoothing["detected_transition_count"] >= 1, smoothing)
    assert_condition(smoothing["smoothed_transition_count"] >= 1, smoothing)
    assert_condition(float(provider["voice_settings"]["stability"]) >= 0.56, provider["voice_settings"])
    assert_condition(float(provider["voice_settings"]["style"]) <= 0.18, provider["voice_settings"])
    assert_condition(provider["rendered_text"] == smoothing["source_rendered_text"], smoothing)
    assert_condition(tts["tts_input_text"] == provider["rendered_text"], tts)
    assert_condition(delivery["final_response_unchanged"] is True, delivery)
    assert_condition(delivery["provider_calls_made"] is False, delivery)
    assert_condition(tts["provider_calls_made"] is False, tts)
    assert_condition(tts["customer_audio_uploaded"] is False, tts)
    assert_condition(tts["voice_cloning_used"] is False, tts)


def validate_german_runtime_smoothing() -> None:
    payload = run_resp_003(
        campaign="campaign-prod-005-b2c-telecom",
        transcript="Das klingt zu teuer und ich weiss nicht, ob sich der Aufwand lohnt.",
        out_name="de-runtime",
    )
    delivery = payload["voice_delivery"]
    smoothing = delivery["voice_emotion_smoothing"]
    provider = delivery["provider_rendering"]

    assert_condition(smoothing["language"] == "de", smoothing)
    assert_condition(smoothing["validation"]["passed"] is True, smoothing["validation"])
    assert_condition(smoothing["transition_smoothing_applied"] is True, smoothing)
    assert_condition(float(provider["voice_settings"]["stability"]) >= 0.56, provider["voice_settings"])
    assert_condition(float(provider["voice_settings"]["speed"]) == 1.065, provider["voice_settings"])
    assert_condition("Das verstehe ich, <break time=\"0.08s\" /> also geht's" in provider["rendered_text"], provider["rendered_text"])


def validate_protected_text_unchanged() -> None:
    payload = run_resp_003(
        campaign="campaign-prod-005-b2c-telecom",
        transcript="Rufen Sie mich bitte nicht mehr an.",
        out_name="protected-runtime",
    )
    delivery = payload["voice_delivery"]
    smoothing = delivery["voice_emotion_smoothing"]
    provider = delivery["provider_rendering"]

    assert_condition(delivery["segments"][0]["segment_type"] == "do_not_call", delivery["segments"])
    assert_condition(smoothing["eligible_for_smoothing"] is False, smoothing)
    assert_condition(smoothing["transition_smoothing_applied"] is False, smoothing)
    assert_condition(smoothing["validation"]["protected_segment_text_changes"] == [], smoothing["validation"])
    assert_condition(provider["rendered_text"] == payload["final_response"], provider)
    assert_condition(provider["voice_settings"].get("speed", 1.0) == 1.0, provider["voice_settings"])


def validate_direct_overemotional_blocking() -> None:
    module = load_module()
    provider_rendering = {
        "provider_key": "elevenlabs",
        "rendered_text": "I understand. This is exciting. Let us keep it simple.",
        "voice_settings": {
            "stability": 0.35,
            "similarity_boost": 0.75,
            "style": 0.82,
            "use_speaker_boost": True,
            "speed": 1.11,
        },
        "segment_renderings": [
            {
                "segment_id": "synthetic-freeform",
                "segment_type": "freeform_objection_handling",
                "protected_reason": None,
                "eligible_for_prosody": True,
                "rendered_text": "I understand. This is exciting. Let us keep it simple.",
            }
        ],
        "api_call_made": False,
        "requires_api_key": False,
        "customer_audio_uploaded": False,
        "voice_cloning_used": False,
        "generated_audio_created": False,
    }
    context = {
        "decision_snapshot": {"detected_emotion": "positive"},
        "speech_interaction": {
            "interaction_markers": [
                {"marker_id": "m1", "pitch_intent": "excited-high", "marker_type": "test"},
                {"marker_id": "m2", "pitch_intent": "steady-low", "marker_type": "test"},
            ]
        },
        "prosody": {
            "prosody_plan": [
                {"cue_id": "p1", "type": "pitch", "direction": "slight-rise", "segment_id": "synthetic-freeform"},
                {"cue_id": "p2", "type": "pitch", "direction": "steady-low", "segment_id": "synthetic-freeform"},
            ]
        },
    }
    result = module.apply_voice_emotion_smoothing(
        {},
        provider_rendering,
        voice_context=context,
        language="en",
        seed="voice-037-direct-test",
    )
    smoothed_settings = result["smoothed_provider_rendering"]["voice_settings"]

    assert_condition(result["blocked_overemotional_cue_count"] >= 1, result)
    assert_condition(result["detected_transition_count"] >= 1, result)
    assert_condition(result["transition_smoothing_applied"] is True, result)
    assert_condition(float(smoothed_settings["stability"]) >= 0.56, smoothed_settings)
    assert_condition(float(smoothed_settings["style"]) <= 0.18, smoothed_settings)
    assert_condition(float(smoothed_settings["speed"]) == 1.11, smoothed_settings)
    assert_condition(result["smoothed_provider_rendering"]["rendered_text"] == provider_rendering["rendered_text"], result)
    assert_condition(result["validation"]["passed"] is True, result["validation"])


def validate_standalone_runner() -> None:
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--out-dir",
            str(VOICE_037_OUT_DIR),
            "--print-json",
        ]
    )
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    payload = parse_stdout_json(completed)
    assert_condition(payload["voice_milestone"] == "VOICE-037", payload)
    assert_condition(payload["summary"]["case_count"] >= 3, payload["summary"])
    assert_condition(payload["summary"]["validation_passed"] == payload["summary"]["case_count"], payload["summary"])
    assert_condition(payload["summary"]["transition_smoothed_cases"] >= 2, payload["summary"])
    assert_condition(payload["summary"]["protected_case_count"] >= 1, payload["summary"])
    assert_condition(payload["summary"]["provider_calls_made"] is False, payload["summary"])
    assert_condition(payload["summary"]["customer_audio_uploaded"] is False, payload["summary"])
    assert_condition(payload["summary"]["voice_cloning_used"] is False, payload["summary"])
    assert_condition((VOICE_037_OUT_DIR / "results.json").exists(), "VOICE-037 runner did not write JSON.")
    assert_condition((VOICE_037_OUT_DIR / "report.md").exists(), "VOICE-037 runner did not write report.")


def main() -> None:
    validate_required_files()
    validate_english_runtime_smoothing()
    validate_german_runtime_smoothing()
    validate_protected_text_unchanged()
    validate_direct_overemotional_blocking()
    validate_standalone_runner()
    print("VOICE-037 emotion transition smoothing validation passed.")


if __name__ == "__main__":
    main()
