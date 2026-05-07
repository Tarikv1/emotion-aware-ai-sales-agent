#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
from typing import Any


VOICE_031_ID = "VOICE-031-reviewed-feature-runtime-mapping"
SOURCE_REVIEW_MILESTONE = "VOICE-030D"

ALLOWED_RUNTIME_CANDIDATE_FEATURES = [
    "speech_burst_count",
    "energy_variation",
    "mean_speech_rms",
]

BLOCKED_RUNTIME_FEATURES = [
    "pause_ratio",
    "average_pause_ms",
    "longest_pause_ms",
    "silence_seconds",
]

FORBIDDEN_SOURCE_BOUNDARY_FLAGS = [
    "provider_calls_made",
    "transcription_created",
    "voice_cloning_used",
    "runtime_profile_applied",
    "public_artifact_created",
]


class MappingPolicyError(ValueError):
    """Raised when a reviewed feature summary is unsafe to map toward runtime."""


def _avg(summary: dict[str, Any]) -> float | None:
    value = summary.get("avg")
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _classify_speech_bursts(summary: dict[str, Any]) -> str:
    value = _avg(summary)
    if value is None:
        return "insufficient_evidence"
    if value >= 12:
        return "higher_turn_density_candidate"
    if value >= 7:
        return "moderate_turn_density_candidate"
    return "lower_turn_density_candidate"


def _classify_energy_variation(summary: dict[str, Any]) -> str:
    value = _avg(summary)
    if value is None:
        return "insufficient_evidence"
    if value >= 0.30:
        return "higher_expressiveness_variation_candidate"
    if value >= 0.18:
        return "moderate_expressiveness_variation_candidate"
    return "low_expressiveness_variation_candidate"


def _classify_mean_rms(summary: dict[str, Any]) -> str:
    value = _avg(summary)
    if value is None:
        return "insufficient_evidence"
    if value >= 0.23:
        return "stronger_presence_candidate"
    if value >= 0.14:
        return "moderate_presence_candidate"
    return "lower_presence_candidate"


def _proposal_for_feature(feature: str, summary: dict[str, Any]) -> dict[str, Any]:
    if feature == "speech_burst_count":
        return {
            "source_feature": feature,
            "runtime_setting": "rhythm_density_hint",
            "proposal": _classify_speech_bursts(summary),
            "interpretation": (
                "Use only as a reviewed hint for where a professional sales voice can sound more "
                "alive across sentence groups; do not copy owner pause lengths."
            ),
            "value_summary": deepcopy(summary),
            "application_mode": "review_only",
        }
    if feature == "energy_variation":
        return {
            "source_feature": feature,
            "runtime_setting": "expressiveness_variation_hint",
            "proposal": _classify_energy_variation(summary),
            "interpretation": (
                "Use only as a reviewed hint for bounded emotional color and emphasis variation; "
                "campaign guardrails still decide what may be said."
            ),
            "value_summary": deepcopy(summary),
            "application_mode": "review_only",
        }
    if feature == "mean_speech_rms":
        return {
            "source_feature": feature,
            "runtime_setting": "presence_level_hint",
            "proposal": _classify_mean_rms(summary),
            "interpretation": (
                "Use only as a reviewed hint for perceived vocal presence; provider loudness and "
                "campaign tone remain separately configured."
            ),
            "value_summary": deepcopy(summary),
            "application_mode": "review_only",
        }
    raise MappingPolicyError(f"Unsupported runtime candidate feature: {feature}")


def validate_review_summary(review_summary: dict[str, Any]) -> dict[str, Any]:
    milestone = review_summary.get("voice_milestone")
    if milestone != SOURCE_REVIEW_MILESTONE:
        raise MappingPolicyError(
            f"VOICE-031 accepts only {SOURCE_REVIEW_MILESTONE} review summaries, got {milestone!r}."
        )

    candidates = review_summary.get("runtime_candidate_summary", {})
    if not isinstance(candidates, dict):
        raise MappingPolicyError("runtime_candidate_summary must be an object.")

    blocked_in_candidates = sorted(set(candidates) & set(BLOCKED_RUNTIME_FEATURES))
    if blocked_in_candidates:
        raise MappingPolicyError(
            "Blocked diagnostic feature(s) appeared in runtime candidates: "
            + ", ".join(blocked_in_candidates)
        )

    unsupported_candidates = sorted(set(candidates) - set(ALLOWED_RUNTIME_CANDIDATE_FEATURES))
    if unsupported_candidates:
        raise MappingPolicyError(
            "Unsupported runtime candidate feature(s): " + ", ".join(unsupported_candidates)
        )

    privacy = review_summary.get("privacy_boundary", {})
    boundary_violations = [
        flag
        for flag in FORBIDDEN_SOURCE_BOUNDARY_FLAGS
        if privacy.get(flag) is True
    ]
    if boundary_violations:
        raise MappingPolicyError(
            "Source review summary already crossed forbidden boundary flag(s): "
            + ", ".join(boundary_violations)
        )

    review_decision = review_summary.get("review_decision", {})
    if review_decision.get("runtime_settings_changed") is True:
        raise MappingPolicyError("VOICE-031 requires source review summaries with no runtime settings changed.")

    diagnostic_only = review_summary.get("diagnostic_only_summary", {})
    excluded = diagnostic_only.get("excluded_from_runtime_learning", [])
    missing_blocked = sorted(set(BLOCKED_RUNTIME_FEATURES) - set(excluded))
    return {
        "passed": not missing_blocked,
        "blocked_feature_violations": blocked_in_candidates,
        "unsupported_candidate_features": unsupported_candidates,
        "missing_blocked_feature_exclusions": missing_blocked,
        "source_boundary_violations": boundary_violations,
    }


def default_deferred_reminders() -> list[dict[str, Any]]:
    return [
        {
            "reminder_id": "whatsapp_voice_note_import",
            "idea": "Optionally import selected Tarik WhatsApp voice notes as extra private speech samples.",
            "why_deferred": (
                "The sample source should be mixed in only after the VOICE-030D review decision, "
                "so the first review is not muddied by multiple recording contexts."
            ),
            "unlock_condition": (
                "After Tarik decides to run VOICE-030D on enough local speech samples, remind him "
                "that WhatsApp voice notes can be imported if he wants more coverage."
            ),
            "privacy_boundary": [
                "selected files stay under data/private/",
                "source label must mark them as whatsapp_voice_note",
                "local conversion is required for non-WAV formats",
                "do not upload private voice notes to providers",
            ],
        }
    ]


def build_runtime_mapping_plan(
    review_summary: dict[str, Any],
    *,
    source_label: str = "synthetic_public_fixture",
    private_review_summary_read: bool = False,
    outputs_stay_under_data_private: bool = False,
    deferred_reminders: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    validation = validate_review_summary(review_summary)
    candidate_summary = review_summary.get("runtime_candidate_summary", {})
    proposals = [
        _proposal_for_feature(feature, candidate_summary[feature])
        for feature in ALLOWED_RUNTIME_CANDIDATE_FEATURES
        if feature in candidate_summary
    ]

    passed = validation["passed"] and len(proposals) > 0
    return {
        "voice_milestone": "VOICE-031",
        "mapping_id": VOICE_031_ID,
        "source_review_milestone": SOURCE_REVIEW_MILESTONE,
        "source_label": source_label,
        "mapping_status": "proposal_only_needs_human_review",
        "runtime_profile_applied": False,
        "human_review_required": True,
        "allowed_runtime_candidate_features": ALLOWED_RUNTIME_CANDIDATE_FEATURES,
        "blocked_runtime_features": BLOCKED_RUNTIME_FEATURES,
        "candidate_mapping_proposals": proposals,
        "campaign_application_policy": {
            "default_voice_posture": "professional_sales_agent",
            "campaign_override_required": True,
            "campaign_can_disable_personalization": True,
            "protected_segments_locked": True,
            "vertical_agnostic_core_preserved": True,
            "applies_to": "campaign-level voice settings only after review, never raw automatic cloning",
        },
        "personalization_guardrails": [
            "do_not_clone_or_overfit_to_one_speaker_identity",
            "do_not_force_every_campaign_to_match_tarik_exactly",
            "preserve_campaign_language_voice_and_target_accent_choice",
            "do_not_turn_diagnostic_pause_metrics_into_agent_pacing_targets",
            "do_not_apply_to_protected_campaign_questions_disclosures_handoff_or_hangup_text",
        ],
        "privacy_boundary": {
            "private_review_summary_read": private_review_summary_read,
            "outputs_stay_under_data_private": outputs_stay_under_data_private,
            "provider_calls_made": False,
            "transcription_created": False,
            "voice_cloning_used": False,
            "runtime_profile_applied": False,
            "raw_audio_read": False,
            "raw_audio_paths_exported": False,
            "public_artifact_created_from_private_summary": False,
        },
        "deferred_reminders": deferred_reminders or default_deferred_reminders(),
        "validation": {
            **validation,
            "passed": passed,
            "proposal_count": len(proposals),
            "notes": (
                "Reviewed feature summary can become a human-reviewed runtime proposal, but nothing "
                "is applied automatically."
                if passed
                else "Reviewed feature summary is not ready for a runtime proposal."
            ),
        },
    }
