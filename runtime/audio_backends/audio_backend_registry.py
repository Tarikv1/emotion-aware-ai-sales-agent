"""Data-only loader and shape checker for audio backend candidates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime.audio_backends.audio_backend_contracts import (
    BACKEND_CATEGORIES,
    INTEGRATION_CLASSIFICATIONS,
    REQUIRED_BACKEND_FIELDS,
    SOURCE_GROUNDING_FIELDS,
)


ROOT = Path(__file__).resolve().parents[2]
CANDIDATES_PATH = ROOT / "runtime" / "audio_backends" / "audio_backend_candidates.json"


def load_audio_backend_registry(path: Path = CANDIDATES_PATH) -> dict[str, Any]:
    """Load the repo-local audio backend registry without side effects."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Audio backend registry must be a JSON object.")
    return payload


def list_audio_backend_candidates(path: Path = CANDIDATES_PATH) -> list[dict[str, Any]]:
    payload = load_audio_backend_registry(path)
    candidates = payload.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("Audio backend registry candidates must be a list.")
    return [item for item in candidates if isinstance(item, dict)]


def get_audio_backend_candidate(backend_id: str, path: Path = CANDIDATES_PATH) -> dict[str, Any]:
    for candidate in list_audio_backend_candidates(path):
        if candidate.get("backend_id") == backend_id:
            return candidate
    raise KeyError(f"Unknown audio backend candidate: {backend_id}")


def validate_audio_backend_candidate_shape(candidate: dict[str, Any]) -> list[str]:
    """Return validation failures for a single candidate.

    This validates metadata shape only. It does not verify remote sources,
    install packages, download model weights, or run inference.
    """

    failures: list[str] = []
    backend_id = str(candidate.get("backend_id") or "<missing>")
    for field_name in REQUIRED_BACKEND_FIELDS + SOURCE_GROUNDING_FIELDS:
        if field_name not in candidate:
            failures.append(f"{backend_id} missing field: {field_name}")

    categories = candidate.get("backend_categories")
    if not isinstance(categories, list) or not categories:
        failures.append(f"{backend_id} backend_categories must be a non-empty list")
    else:
        unknown = sorted(str(item) for item in categories if item not in BACKEND_CATEGORIES)
        if unknown:
            failures.append(f"{backend_id} unknown backend_categories: {unknown}")

    classification = candidate.get("integration_classification")
    if classification not in INTEGRATION_CLASSIFICATIONS:
        failures.append(f"{backend_id} invalid integration_classification: {classification!r}")

    source_evidence = candidate.get("source_evidence")
    if not isinstance(source_evidence, list) or not source_evidence:
        failures.append(f"{backend_id} must include source_evidence")
    else:
        for index, evidence in enumerate(source_evidence, start=1):
            if not isinstance(evidence, dict):
                failures.append(f"{backend_id} source_evidence[{index}] must be an object")
                continue
            if not str(evidence.get("url") or "").strip():
                failures.append(f"{backend_id} source_evidence[{index}] missing url")
            if not str(evidence.get("fact") or "").strip():
                failures.append(f"{backend_id} source_evidence[{index}] missing fact")

    if candidate.get("live_runtime_allowed") is not False and backend_id != "elevenlabs_existing_provider":
        failures.append(f"{backend_id} must not be live-runtime allowed in Phase 4I0")
    if candidate.get("model_weights_download_required") is True and candidate.get("model_weights_available") == "unknown":
        failures.append(f"{backend_id} cannot require model weights while model_weights_available is unknown")
    return failures
