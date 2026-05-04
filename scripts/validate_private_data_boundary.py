#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


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


def read_text(relative_path: str) -> str:
    path = ROOT / relative_path
    assert_condition(path.is_file(), f"Missing required file: {relative_path}")
    return path.read_text(encoding="utf-8")


def validate_gitignore() -> None:
    root_gitignore = read_text(".gitignore")
    assert_condition("data/private/*" in root_gitignore, "Root .gitignore must ignore data/private/*.")
    assert_condition(
        "!data/private/.gitignore" in root_gitignore,
        "Root .gitignore must allow only data/private/.gitignore.",
    )

    private_gitignore_path = ROOT / "data" / "private" / ".gitignore"
    assert_condition(private_gitignore_path.is_file(), "data/private/.gitignore is missing.")
    private_lines = private_gitignore_path.read_text(encoding="utf-8").splitlines()
    assert_condition("*" in private_lines, "data/private/.gitignore must ignore all private files.")
    assert_condition(
        "!.gitignore" in private_lines,
        "data/private/.gitignore must allow itself to remain tracked.",
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


def main() -> None:
    assert_condition((ROOT / "data" / "private").is_dir(), "data/private/ folder is missing.")
    validate_gitignore()
    validate_docs()
    validate_guard_does_not_scan_private_data()
    print("Private data boundary validation passed.")


if __name__ == "__main__":
    main()
