#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
import json
import subprocess
import sys
from pathlib import Path

from voice_private_pattern_profile import apply_voice_private_pattern_profile


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_voice_041_private_pattern_profile.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "voice-041-private-pattern-profile.json"
TMP_DIR = ROOT / ".tmp" / "voice-041-validation"
RESULT_PATH = TMP_DIR / "result.json"
REPORT_PATH = TMP_DIR / "report.md"


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def base_rendering(*, protected: bool = False) -> dict:
    segment_type = "do_not_call" if protected else "freeform_objection_handling"
    return {
        "provider_key": "elevenlabs",
        "provider_name": "ElevenLabs Flash v2.5",
        "rendered_text": "I get why you would ask that, so I will keep this practical.",
        "voice_settings": {
            "stability": 0.45,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True,
            "speed": 1.12,
        },
        "segment_renderings": [
            {
                "segment_id": "resp-002-final-response",
                "segment_type": segment_type,
                "protected_reason": "policy_or_compliance_boundary" if protected else None,
                "eligible_for_prosody": not protected,
                "plain_text": "I get why you would ask that, so I will keep this practical.",
                "rendered_text": "I get why you would ask that, so I will keep this practical.",
                "provider_tags_inserted": [],
            }
        ],
        "api_call_made": False,
        "requires_api_key": False,
        "customer_audio_uploaded": False,
        "voice_cloning_used": False,
        "generated_audio_created": False,
    }


def accepted_campaign() -> dict:
    return {
        "campaign_id": "voice-041-validation",
        "language": "en",
        "voice_private_pattern_profile": {
            "enabled": True,
            "review_status": "accepted",
            "source_review_milestone": "VOICE-031",
            "source_kind": "abstract_private_speech_patterns",
            "rhythm_density_hint": "higher_turn_density_candidate",
            "expressiveness_variation_hint": "higher_expressiveness_variation_candidate",
            "presence_level_hint": "lower_presence_candidate",
        },
    }


def validate_accepted_profile_applies_only_settings() -> None:
    source = base_rendering()
    result = apply_voice_private_pattern_profile(
        accepted_campaign(),
        source,
        language="en",
        seed="voice-041-validation",
    )
    profiled = result["profiled_provider_rendering"]
    settings = profiled["voice_settings"]

    assert_condition(result["voice_milestone"] == "VOICE-041", "Unexpected milestone.")
    assert_condition(result["enabled"] is True, "Accepted profile should be enabled.")
    assert_condition(result["applied"] is True, result)
    assert_condition(result["eligible_segment_count"] == 1, result)
    assert_condition(profiled["rendered_text"] == source["rendered_text"], "VOICE-041 must not rewrite text.")
    assert_condition(
        profiled["segment_renderings"][0]["rendered_text"] == source["segment_renderings"][0]["rendered_text"],
        "VOICE-041 must not rewrite segment text.",
    )
    assert_condition(settings["style"] == 0.06, settings)
    assert_condition(settings["stability"] == 0.44, settings)
    assert_condition(settings["speed"] == source["voice_settings"]["speed"], "VOICE-041 must not change accepted pacing.")
    assert_condition(settings["similarity_boost"] == source["voice_settings"]["similarity_boost"], settings)
    assert_condition(result["presence_action"] == "blocked_low_presence_copy", result)
    assert_condition(result["rhythm_density_action"] == "metadata_only_no_pacing_change", result)
    assert_condition(result["validation"]["passed"] is True, result["validation"])
    assert_condition(result["runtime_boundary"]["provider_calls_made"] is False, result["runtime_boundary"])
    assert_condition(result["runtime_boundary"]["voice_cloning_used"] is False, result["runtime_boundary"])
    assert_condition(result["runtime_boundary"]["raw_audio_read"] is False, result["runtime_boundary"])


def validate_protected_segment_blocks_profile() -> None:
    source = base_rendering(protected=True)
    result = apply_voice_private_pattern_profile(
        accepted_campaign(),
        source,
        language="en",
        seed="voice-041-validation-protected",
    )
    assert_condition(result["applied"] is False, result)
    assert_condition(result["blocked_reason"] == "protected_or_ineligible_segment_present", result)
    assert_condition(result["profiled_provider_rendering"] == source, "Protected rendering should remain unchanged.")
    assert_condition(result["validation"]["passed"] is True, result["validation"])


def validate_unaccepted_profile_blocks_profile() -> None:
    campaign = accepted_campaign()
    campaign["voice_private_pattern_profile"] = deepcopy(campaign["voice_private_pattern_profile"])
    campaign["voice_private_pattern_profile"]["review_status"] = "needs_human_review"
    result = apply_voice_private_pattern_profile(
        campaign,
        base_rendering(),
        language="en",
        seed="voice-041-validation-unaccepted",
    )
    assert_condition(result["enabled"] is True, result)
    assert_condition(result["applied"] is False, result)
    assert_condition(result["blocked_reason"] == "profile_not_human_accepted", result)
    assert_condition(result["validation"]["passed"] is True, result["validation"])


def validate_disabled_profile_is_noop() -> None:
    campaign = {"campaign_id": "voice-041-disabled", "language": "en"}
    source = base_rendering()
    result = apply_voice_private_pattern_profile(
        campaign,
        source,
        language="en",
        seed="voice-041-validation-disabled",
    )
    assert_condition(result["enabled"] is False, result)
    assert_condition(result["applied"] is False, result)
    assert_condition(result["profiled_provider_rendering"] == source, "Disabled profile should be a no-op.")
    assert_condition(result["validation"]["passed"] is True, result["validation"])


def validate_runner_checkpoint() -> None:
    assert_condition(RUNNER.exists(), "VOICE-041 runner is missing.")
    assert_condition(CASE_PATH.exists(), "VOICE-041 case file is missing.")
    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--out",
            str(RESULT_PATH),
            "--report-out",
            str(REPORT_PATH),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    payload = json.loads(completed.stdout)
    assert_condition(payload["voice_private_pattern_profile_runtime_id"] == "VOICE-041-private-pattern-profile", payload)
    assert_condition(payload["summary"]["case_count"] == 2, payload["summary"])
    assert_condition(payload["summary"]["applied_count"] == 1, payload["summary"])
    assert_condition(payload["summary"]["blocked_count"] == 1, payload["summary"])
    assert_condition(payload["summary"]["provider_calls_made"] is False, payload["summary"])
    assert_condition(payload["summary"]["voice_cloning_used"] is False, payload["summary"])
    assert_condition(payload["summary"]["raw_audio_read"] is False, payload["summary"])
    assert_condition(payload["summary"]["validation_passed"] is True, payload["summary"])
    assert_condition(RESULT_PATH.exists(), "VOICE-041 result was not written.")
    assert_condition(REPORT_PATH.exists(), "VOICE-041 report was not written.")


def main() -> None:
    validate_accepted_profile_applies_only_settings()
    validate_protected_segment_blocks_profile()
    validate_unaccepted_profile_blocks_profile()
    validate_disabled_profile_is_noop()
    validate_runner_checkpoint()
    print("VOICE-041 private pattern profile validation passed.")


if __name__ == "__main__":
    main()
