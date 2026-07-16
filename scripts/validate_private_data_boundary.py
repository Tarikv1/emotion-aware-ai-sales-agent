#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

try:
    from scripts.emotion_state_phase_a_verification_evidence import (
        PRIVATE_GITIGNORE_SENTINEL_BYTES,
        read_tracked_private_gitignore_sentinel,
    )
except ModuleNotFoundError:
    from emotion_state_phase_a_verification_evidence import (
        PRIVATE_GITIGNORE_SENTINEL_BYTES,
        read_tracked_private_gitignore_sentinel,
    )


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_POLICY_PHRASES = {
    "docs/data/PRIVATE_CALL_CENTER_DATA_POLICY.md": [
        "Raw private call-center audio must live only in:",
        "data/private/",
        "Private identifiers are not training signal.",
        "Export Review Gate",
        "Training Signal Boundary",
        "Nothing derived from private call-center audio may leave `data/private/` until it passes a local export review.",
    ],
    "docs/data/PRIVATE_CALL_LEARNING_PIPELINE.md": [
        "Raw private audio never leaves `data/private/`",
        "Private identifiers are not training signal",
        "Pattern-mining first, fine-tuning later",
        "No safe export before redaction and human review",
    ],
    "docs/data/DATA_USAGE_POLICY.md": [
        "Store private raw call-center audio in `data/private/`",
        "Treat private identifiers as non-training signal.",
        "Only reviewed, minimized, non-identifying sales-pattern artifacts may leave `data/private/`.",
    ],
    "AGENTS.md": [
        "Raw private call-center audio belongs only in `data/private/`",
        "assume it never leaves Tarik's local machine",
    ],
    "README.md": [
        "`data/private/`: local-only private call-center audio and raw private call assets.",
    ],
    "docs/thesis/ROADMAP.md": [
        "private identifiers are removed as non-training signal",
    ],
}


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_text(relative_path: str, root: Path = ROOT) -> str:
    path = root / relative_path
    assert_condition(path.is_file(), f"Missing required file: {relative_path}")
    return path.read_text(encoding="utf-8")


def validate_gitignore(root: Path = ROOT) -> None:
    root_gitignore = read_text(".gitignore", root)
    assert_condition("data/private/*" in root_gitignore, "Root .gitignore must ignore data/private/*.")
    assert_condition(
        "!data/private/.gitignore" in root_gitignore,
        "Root .gitignore must allow only data/private/.gitignore.",
    )

    assert_condition(
        read_tracked_private_gitignore_sentinel(root)
        == PRIVATE_GITIGNORE_SENTINEL_BYTES,
        "Tracked data/private/.gitignore bytes do not match the private workspace contract.",
    )


def validate_docs() -> None:
    for relative_path, phrases in REQUIRED_POLICY_PHRASES.items():
        text = read_text(relative_path)
        for phrase in phrases:
            assert_condition(phrase in text, f"Missing private-data boundary phrase in {relative_path}: {phrase}")


def validate_guard_does_not_scan_private_data() -> None:
    guard_text = read_text("scripts/check_project_drift.py")
    assert_condition(
        '("data", "private")' in guard_text,
        "Project drift guard must skip data/private/ contents.",
    )
    assert_condition(
        '"data/private/.gitignore"' in guard_text,
        "Project drift guard must require data/private/.gitignore.",
    )
    assert_condition(
        '"docs/data/PRIVATE_CALL_CENTER_DATA_POLICY.md"' in guard_text,
        "Project drift guard must require the private call-center data policy.",
    )
    assert_condition(
        '"docs/data/PRIVATE_CALL_LEARNING_PIPELINE.md"' in guard_text,
        "Project drift guard must require the private call learning pipeline policy.",
    )


def main() -> None:
    validate_gitignore()
    validate_docs()
    validate_guard_does_not_scan_private_data()
    print("Private data boundary validation passed.")


if __name__ == "__main__":
    main()
