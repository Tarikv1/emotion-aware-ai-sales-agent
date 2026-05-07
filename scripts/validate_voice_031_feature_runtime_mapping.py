#!/usr/bin/env python3
from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
RUNNER = SCRIPT_DIR / "run_voice_031_feature_runtime_mapping.py"
MODULE = SCRIPT_DIR / "voice_feature_runtime_mapping.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "voice-031-feature-runtime-mapping.json"
DOC_PATH = ROOT / "docs" / "product" / "VOICE_031_FEATURE_RUNTIME_MAPPING.md"
TMP_DIR = ROOT / ".tmp" / "voice-031-validation"
PUBLIC_OUT_DIR = TMP_DIR / "public"
PRIVATE_ROOT = ROOT / "data" / "private" / "voice-031-validation"
PRIVATE_SUMMARY = PRIVATE_ROOT / "derived" / "review" / "voice-030d-feature-review-summary.json"
PRIVATE_OUT_DIR = PRIVATE_ROOT / "derived" / "review" / "voice-031-runtime-mapping"


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=30)


def write_private_summary() -> None:
    PRIVATE_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "voice_milestone": "VOICE-030D",
        "summary": {
            "sample_count": 3,
            "language_counts": {"en": 3},
            "duration_seconds": {"count": 3, "min": 5.0, "max": 8.0, "avg": 6.5},
            "duration_is_context_only": True,
        },
        "runtime_candidate_summary": {
            "speech_burst_count": {"count": 3, "min": 7, "max": 12, "avg": 9.333},
            "energy_variation": {"count": 3, "min": 0.18, "max": 0.34, "avg": 0.263},
            "mean_speech_rms": {"count": 3, "min": 0.16, "max": 0.24, "avg": 0.203},
        },
        "diagnostic_only_summary": {
            "excluded_from_runtime_learning": [
                "pause_ratio",
                "average_pause_ms",
                "longest_pause_ms",
                "silence_seconds",
            ],
            "reason": "Owner formulation pauses are not runtime pacing targets.",
        },
        "review_decision": {
            "status": "needs_human_review",
            "runtime_settings_changed": False,
        },
        "privacy_boundary": {
            "private_input_read": True,
            "outputs_stay_under_data_private": True,
            "provider_calls_made": False,
            "transcription_created": False,
            "voice_cloning_used": False,
            "runtime_profile_applied": False,
            "public_artifact_created": False,
            "raw_audio_paths_exported": False,
            "human_review_required_before_runtime_use": True,
        },
    }
    PRIVATE_SUMMARY.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def import_mapping_module():
    sys.path.insert(0, str(SCRIPT_DIR))
    return importlib.import_module("voice_feature_runtime_mapping")


def validate_required_files() -> None:
    for path in [RUNNER, MODULE, CASE_PATH, DOC_PATH]:
        assert_condition(path.exists(), f"Required VOICE-031 file is missing: {path.relative_to(ROOT)}")


def validate_public_synthetic_run() -> None:
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--out-dir",
            str(PUBLIC_OUT_DIR),
            "--print-json",
        ]
    )
    assert_condition(completed.returncode == 0, completed.stderr or completed.stdout)
    payload = json.loads(completed.stdout)
    result_path = PUBLIC_OUT_DIR / "results.json"
    report_path = PUBLIC_OUT_DIR / "report.md"
    assert_condition(result_path.exists(), "VOICE-031 public synthetic JSON result was not written.")
    assert_condition(report_path.exists(), "VOICE-031 public synthetic report was not written.")

    assert_condition(payload["voice_milestone"] == "VOICE-031", "Unexpected milestone.")
    assert_condition(payload["source_review_milestone"] == "VOICE-030D", "Unexpected source milestone.")
    assert_condition(payload["mapping_status"] == "proposal_only_needs_human_review", payload)
    assert_condition(payload["runtime_profile_applied"] is False, "VOICE-031 must not apply runtime settings.")
    assert_condition(payload["human_review_required"] is True, "VOICE-031 must require human review.")
    assert_condition(payload["validation"]["passed"] is True, payload["validation"])

    boundary = payload["privacy_boundary"]
    assert_condition(boundary["private_review_summary_read"] is False, "Default run should use public synthetic fixture.")
    assert_condition(boundary["provider_calls_made"] is False, "VOICE-031 must not call providers.")
    assert_condition(boundary["transcription_created"] is False, "VOICE-031 must not transcribe.")
    assert_condition(boundary["voice_cloning_used"] is False, "VOICE-031 must not clone voices.")
    assert_condition(boundary["runtime_profile_applied"] is False, "VOICE-031 must not apply runtime profiles.")

    allowed = payload["allowed_runtime_candidate_features"]
    assert_condition(
        allowed == ["speech_burst_count", "energy_variation", "mean_speech_rms"],
        f"Unexpected allowed runtime candidates: {allowed}",
    )
    for key in ["pause_ratio", "average_pause_ms", "longest_pause_ms", "silence_seconds"]:
        assert_condition(key in payload["blocked_runtime_features"], f"{key} should be explicitly blocked.")

    proposal_sources = {proposal["source_feature"] for proposal in payload["candidate_mapping_proposals"]}
    assert_condition(proposal_sources == set(allowed), f"Unexpected proposal sources: {proposal_sources}")
    assert_condition(
        not (proposal_sources & set(payload["blocked_runtime_features"])),
        "Blocked diagnostic features must not be mapped into runtime proposals.",
    )
    setting_ids = {proposal["runtime_setting"] for proposal in payload["candidate_mapping_proposals"]}
    for setting in ["rhythm_density_hint", "expressiveness_variation_hint", "presence_level_hint"]:
        assert_condition(setting in setting_ids, f"Missing proposal setting: {setting}")

    campaign_policy = payload["campaign_application_policy"]
    assert_condition(campaign_policy["default_voice_posture"] == "professional_sales_agent", campaign_policy)
    assert_condition(campaign_policy["campaign_override_required"] is True, campaign_policy)
    assert_condition(campaign_policy["protected_segments_locked"] is True, campaign_policy)
    assert_condition(campaign_policy["vertical_agnostic_core_preserved"] is True, campaign_policy)

    reminders = payload["deferred_reminders"]
    whatsapp = [item for item in reminders if item["reminder_id"] == "whatsapp_voice_note_import"]
    assert_condition(whatsapp, "VOICE-031 should preserve the WhatsApp import reminder.")
    assert_condition("VOICE-030D" in whatsapp[0]["unlock_condition"], whatsapp[0])

    report_text = report_path.read_text(encoding="utf-8")
    assert_condition("proposal only" in report_text.lower(), "Report should state this is proposal only.")
    assert_condition("WhatsApp" in report_text, "Report should mention the deferred WhatsApp reminder.")


def validate_private_review_guards() -> None:
    write_private_summary()
    without_flag = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--summary-json",
            str(PRIVATE_SUMMARY),
            "--out-dir",
            str(PRIVATE_OUT_DIR),
            "--print-json",
        ]
    )
    assert_condition(without_flag.returncode != 0, "Private review summary should require explicit opt-in.")
    assert_condition(
        "--allow-private-review-read" in (without_flag.stderr + without_flag.stdout),
        "Private-read refusal should explain the required flag.",
    )

    public_output = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--summary-json",
            str(PRIVATE_SUMMARY),
            "--allow-private-review-read",
            "--out-dir",
            str(PUBLIC_OUT_DIR / "private-leak"),
            "--print-json",
        ]
    )
    assert_condition(
        public_output.returncode != 0,
        "Private-derived VOICE-031 mapping output must not be written outside data/private.",
    )
    assert_condition("data/private" in (public_output.stderr + public_output.stdout), "Refusal should mention data/private.")

    private_output = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--summary-json",
            str(PRIVATE_SUMMARY),
            "--allow-private-review-read",
            "--out-dir",
            str(PRIVATE_OUT_DIR),
            "--print-json",
        ]
    )
    assert_condition(private_output.returncode == 0, private_output.stderr or private_output.stdout)
    payload = json.loads(private_output.stdout)
    assert_condition(payload["privacy_boundary"]["private_review_summary_read"] is True, payload["privacy_boundary"])
    assert_condition(payload["privacy_boundary"]["outputs_stay_under_data_private"] is True, payload["privacy_boundary"])
    assert_condition(payload["runtime_profile_applied"] is False, "Private summary must still not auto-apply runtime settings.")


def validate_blocked_feature_rejection() -> None:
    module = import_mapping_module()
    blocked_summary = {
        "voice_milestone": "VOICE-030D",
        "runtime_candidate_summary": {
            "speech_burst_count": {"count": 2, "avg": 9.0},
            "pause_ratio": {"count": 2, "avg": 0.5},
        },
        "diagnostic_only_summary": {
            "excluded_from_runtime_learning": [
                "pause_ratio",
                "average_pause_ms",
                "longest_pause_ms",
                "silence_seconds",
            ],
        },
        "privacy_boundary": {
            "provider_calls_made": False,
            "transcription_created": False,
            "voice_cloning_used": False,
            "runtime_profile_applied": False,
            "public_artifact_created": False,
        },
    }
    try:
        module.build_runtime_mapping_plan(blocked_summary)
    except module.MappingPolicyError as exc:
        assert_condition("pause_ratio" in str(exc), "Blocked feature error should name the blocked feature.")
    else:
        raise AssertionError("VOICE-031 must reject blocked diagnostic features in runtime candidates.")


def main() -> None:
    validate_required_files()
    validate_public_synthetic_run()
    validate_private_review_guards()
    validate_blocked_feature_rejection()
    print("VOICE-031 feature-to-runtime mapping gate validation passed.")


if __name__ == "__main__":
    main()
