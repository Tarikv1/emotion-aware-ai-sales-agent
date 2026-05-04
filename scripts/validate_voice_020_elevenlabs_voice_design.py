#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_voice_020_elevenlabs_voice_design.py"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "voice-020-elevenlabs-voice-design.json"
TMP_DIR = ROOT / ".tmp" / "voice-020-validation"
TMP_JSON = TMP_DIR / "VOICE-020-elevenlabs-voice-design.json"
TMP_REPORT = TMP_DIR / "VOICE-020-elevenlabs-voice-design-report.md"

SECRET_PATTERN = re.compile(
    r"(sk_car_[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|CARTESIA_API_KEY\s*=\s*[^\s]+|ELEVENLABS_API_KEY\s*=\s*[^\s]+|OPENAI_API_KEY\s*=\s*[^\s]+|Authorization:\s*Bearer\s+[A-Za-z0-9]|X-API-Key\s*[:=]\s*[A-Za-z0-9]|xi-api-key\s*[:=]\s*[A-Za-z0-9])"
)

SECRET_VALUES = {
    "ELEVENLABS_API_KEY": "TEST_ELEVENLABS_VALUE_MUST_NOT_APPEAR",
    "ELEVENLABS_VOICE_ID_DE": "test-eleven-de-voice-id-must-not-appear",
    "ELEVENLABS_VOICE_ID_EN": "test-eleven-en-voice-id-must-not-appear",
}


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(SECRET_VALUES)
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env, timeout=30)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_payload(payload: dict, config: dict) -> None:
    expected = config["expected"]
    summary = payload["summary"]
    assert_condition(payload["voice_milestone"] == "VOICE-020", payload["voice_milestone"])
    assert_condition(summary["voice_design_profile_count"] == expected["voice_design_profile_count"], summary)
    assert_condition(summary["languages"] == expected["languages"], summary)
    assert_condition(summary["voice_design_ui_candidate_count"] >= expected["min_voice_design_ui_candidates"], summary)
    assert_condition(summary["voice_remixing_prompt_count"] >= expected["min_voice_remixing_prompts"], summary)
    assert_condition(summary["settings_candidate_count"] >= expected["min_settings_candidates"], summary)
    assert_condition(summary["emotional_delivery_bundle_count"] >= expected["min_emotional_delivery_bundles"], summary)
    assert_condition(summary["provider_calls_made"] is expected["provider_calls_made"], summary)
    assert_condition(summary["requires_api_key"] is expected["requires_api_key"], summary)
    assert_condition(summary["customer_audio_uploaded"] is expected["customer_audio_uploaded"], summary)
    assert_condition(summary["voice_cloning_used"] is expected["voice_cloning_used"], summary)
    assert_condition(summary["generated_audio_created"] is expected["generated_audio_created"], summary)
    assert_condition(summary["quality_claim_allowed"] is expected["quality_claim_allowed"], summary)
    assert_condition(summary["private_audio_uploaded"] is False, summary)
    assert_condition(summary["private_audio_copied_to_generated_artifacts"] is False, summary)

    runtime = payload["runtime_boundary"]
    assert_condition(runtime["offline_design_only"] is True, runtime)
    assert_condition(runtime["provider_calls_made"] is False, runtime)
    assert_condition(runtime["requires_api_key"] is False, runtime)
    assert_condition(runtime["private_audio_uploaded"] is False, runtime)
    assert_condition(runtime["voice_cloning_used"] is False, runtime)

    profiles = payload["voice_design_profiles"]
    assert_condition({profile["language"] for profile in profiles} == {"en", "de"}, profiles)
    for profile in profiles:
        assert_condition(20 <= len(profile["voice_design_prompt"]) <= 1000, profile["profile_id"])
        assert_condition(100 <= len(profile["preview_text"]) <= 1000, profile["profile_id"])
        assert_condition("sales" in profile["voice_design_prompt"].lower(), profile["profile_id"])
        assert_condition("full-band" in profile["voice_design_prompt"].lower(), profile["profile_id"])
        assert_condition("faster-than-normal" in profile["voice_design_prompt"].lower(), profile["profile_id"])
        assert_condition("robotic" in " ".join(profile["avoid_traits"]).lower(), profile["profile_id"])
        assert_condition("telephone" in " ".join(profile["avoid_traits"]).lower(), profile["profile_id"])

    ui_candidate_ids = {candidate["candidate_id"] for candidate in payload["voice_design_ui_candidates"]}
    for required in {"clean-natural-medium-guidance", "creative-less-robotic", "prompt-faithful-clean-sales"}:
        assert_condition(required in ui_candidate_ids, f"Missing Voice Design UI candidate: {required}")
    for candidate in payload["voice_design_ui_candidates"]:
        assert_condition(0 <= candidate["loudness"] <= 1, candidate)
        assert_condition(0 <= candidate["guidance_scale"] <= 1, candidate)

    remix_prompt_ids = {prompt["remix_prompt_id"] for prompt in payload["voice_remixing_prompts"]}
    for required in {"elevenlabs-remix-en-sales-naturalizer-v1", "elevenlabs-remix-de-sales-naturalizer-v1"}:
        assert_condition(required in remix_prompt_ids, f"Missing Voice Remixing prompt: {required}")
    for prompt in payload["voice_remixing_prompts"]:
        assert_condition(prompt["recommended_prompt_strength"] == "Medium", prompt)
        assert_condition(prompt["fallback_prompt_strength_if_too_subtle"] == "High", prompt)
        for category in ["Pacing", "Emotion", "Pitch", "Audio Quality"]:
            assert_condition(category in prompt["categories"], prompt)
        prompt_text = prompt["prompt"].lower()
        assert_condition("less robotic" in prompt_text, prompt["remix_prompt_id"])
        assert_condition("less evenly paced" in prompt_text, prompt["remix_prompt_id"])
        assert_condition("clean" in prompt_text and "full-band" in prompt_text, prompt["remix_prompt_id"])
        assert_condition("faster" in prompt_text, prompt["remix_prompt_id"])
        assert_condition("combine effects" in prompt_text, prompt["remix_prompt_id"])
        assert_condition(250 <= len(prompt["custom_script"]) <= 1000, prompt["remix_prompt_id"])

    candidate_ids = {candidate["candidate_id"] for candidate in payload["settings_matrix"]}
    for required in {"realtime-balanced", "emotional-opening", "clarity-safe", "expressive-quality"}:
        assert_condition(required in candidate_ids, f"Missing settings candidate: {required}")
    for candidate in payload["settings_matrix"]:
        assert_condition(0 <= candidate["stability"] <= 1, candidate)
        assert_condition(0 <= candidate["similarity_boost"] <= 1, candidate)
        assert_condition(0 <= candidate["style"] <= 1, candidate)
        assert_condition(0.7 <= candidate["speed"] <= 1.2, candidate)
        if candidate["candidate_id"] != "expressive-quality":
            assert_condition(candidate["model_family"] == "flash_or_turbo_realtime", candidate)

    protected = payload["protected_text_rules"]
    assert_condition(protected["exact_text_lock"] is True, protected)
    assert_condition(protected["filler_words_allowed"] is False, protected)
    assert_condition(protected["random_spacing_allowed"] is False, protected)
    assert_condition(protected["emotional_overrides_allowed"] is False, protected)
    assert_condition("campaign_qualification_question" in protected["segment_types"], protected)
    assert_condition("required_disclosure" in protected["segment_types"], protected)

    for bundle in payload["emotional_delivery_bundles"]:
        assert_condition(bundle["blocked_in_protected_text"] is True, bundle)
        assert_condition(len(bundle["combined_effects"]) >= 3, bundle)

    private_boundary = payload["private_call_center_boundary"]
    assert_condition(private_boundary["raw_private_audio_provider_upload_allowed"] is False, private_boundary)
    assert_condition(private_boundary["customer_voice_upload_allowed"] is False, private_boundary)
    assert_condition(private_boundary["voice_cloning_allowed"] is False, private_boundary)
    assert_condition("abstract tuning notes" in private_boundary["allowed_use"], private_boundary)


def main() -> None:
    assert_condition(RUNNER.exists(), "VOICE-020 runner is missing.")
    assert_condition(CASES_PATH.exists(), "VOICE-020 case file is missing.")
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--cases",
            str(CASES_PATH),
            "--out",
            str(TMP_JSON),
            "--report-out",
            str(TMP_REPORT),
        ]
    )
    assert_condition(completed.returncode == 0, completed.stderr)
    assert_condition(TMP_JSON.exists(), "VOICE-020 validation JSON was not created.")
    assert_condition(TMP_REPORT.exists(), "VOICE-020 validation report was not created.")

    payload = load_json(TMP_JSON)
    config = load_json(CASES_PATH)
    validate_payload(payload, config)

    first_payload_text = TMP_JSON.read_text(encoding="utf-8")
    completed_again = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--cases",
            str(CASES_PATH),
            "--out",
            str(TMP_JSON),
            "--report-out",
            str(TMP_REPORT),
        ]
    )
    assert_condition(completed_again.returncode == 0, completed_again.stderr)
    assert_condition(first_payload_text == TMP_JSON.read_text(encoding="utf-8"), "VOICE-020 output should be deterministic.")

    combined_output = (
        json.dumps(payload, ensure_ascii=False)
        + TMP_REPORT.read_text(encoding="utf-8")
        + completed.stdout
        + completed.stderr
    )
    for value in SECRET_VALUES.values():
        assert_condition(value not in combined_output, f"Secret test value leaked: {value}")
    match = SECRET_PATTERN.search(combined_output)
    if match is not None:
        raise AssertionError(f"Potential secret-like value found in VOICE-020 output: {match.group(0)!r}")
    print("VOICE-020 ElevenLabs voice design validation passed.")


if __name__ == "__main__":
    main()
