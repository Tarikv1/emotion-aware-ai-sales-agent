"""Contracts for source-grounded audio backend research records.

These contracts are intentionally data-only. They do not import audio
libraries, initialize providers, load model weights, or generate speech.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


BACKEND_CATEGORIES = (
    "provider_tts",
    "local_tts",
    "local_asr",
    "local_speech_to_speech",
    "local_voice_conversion",
    "prosody_control_inspiration",
    "research_only",
    "production_candidate",
)

INTEGRATION_CLASSIFICATIONS = (
    "current_runtime_provider",
    "integration_candidate",
    "benchmark_candidate",
    "architecture_inspiration_only",
    "research_only",
)

REQUIRED_BACKEND_FIELDS = (
    "backend_id",
    "display_name",
    "source_url",
    "repo_url",
    "model_card_url",
    "license_name",
    "license_summary",
    "commercial_use_status",
    "hardware_requirements",
    "windows_support",
    "wsl_or_linux_required",
    "local_install_possible",
    "role_in_project",
    "integration_priority",
    "live_runtime_allowed",
    "provider_calls_required",
    "model_weights_download_required",
    "expected_risks",
    "recommended_next_phase",
)

SOURCE_GROUNDING_FIELDS = (
    "license_url",
    "license_file_path",
    "model_weights_available",
    "capability_classification",
    "integration_classification",
    "source_evidence",
)


@dataclass(frozen=True)
class AudioBackendCandidate:
    """Shape for a source-grounded backend candidate.

    Values that a source does not state should be recorded as "unknown" rather
    than inferred from model names or adjacent projects.
    """

    backend_id: str
    display_name: str
    source_url: str
    repo_url: str
    model_card_url: str
    license_name: str
    license_summary: str
    commercial_use_status: str
    hardware_requirements: str
    windows_support: str
    wsl_or_linux_required: str
    local_install_possible: str
    role_in_project: str
    integration_priority: str
    live_runtime_allowed: bool
    provider_calls_required: bool
    model_weights_download_required: bool
    expected_risks: list[str] = field(default_factory=list)
    recommended_next_phase: str = ""
    backend_categories: list[str] = field(default_factory=list)
    license_url: str = ""
    license_file_path: str = ""
    model_weights_available: str = "unknown"
    capability_classification: list[str] = field(default_factory=list)
    integration_classification: str = "research_only"
    source_evidence: list[dict[str, Any]] = field(default_factory=list)


def required_field_names() -> tuple[str, ...]:
    return REQUIRED_BACKEND_FIELDS


def known_backend_categories() -> tuple[str, ...]:
    return BACKEND_CATEGORIES
