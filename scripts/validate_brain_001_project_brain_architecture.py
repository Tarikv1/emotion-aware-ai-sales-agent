#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ROOT / "docs" / "brain" / "BRAIN_001_PROJECT_BRAIN_ARCHITECTURE.md"

REQUIRED_MARKERS = [
    "# BRAIN-001 Project Brain Architecture",
    "one reusable sales-agent core",
    "SalesCampaign",
    "retrieval disabled by default",
    "RAG-020",
    "RAG-021",
    "advisory-only",
    "short-term call state",
    "No raw private audio",
    "No raw private transcripts",
    "voice-personality selector remains blocked",
    "German pacing-stability follow-up",
    "human handoff",
    "protected text",
]


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    assert_condition(DOC_PATH.exists(), f"Missing BRAIN-001 architecture doc: {DOC_PATH.relative_to(ROOT)}")
    text = DOC_PATH.read_text(encoding="utf-8")
    missing = [marker for marker in REQUIRED_MARKERS if marker not in text]
    assert_condition(not missing, f"BRAIN-001 doc is missing required marker(s): {missing}")
    assert_condition(
        "runtime use requires a separate RAG-017 registry rebuild and RAG-018 guarded-retrieval evaluation" in text,
        "BRAIN-001 must preserve the runtime retrieval promotion gate.",
    )
    assert_condition(
        "not a prompt dump" in text,
        "BRAIN-001 must define the brain as architecture, not a single giant prompt.",
    )
    print("BRAIN-001 project brain architecture validation passed.")


if __name__ == "__main__":
    main()
