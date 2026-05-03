#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

AGENTS_PATH = ROOT / "AGENTS.md"
COMMANDS_PATH = ROOT / "docs" / "product" / "COMMANDS.md"
POLICY_PATH = ROOT / "docs" / "product" / "CONTEXT_READING_POLICY.md"
READER_PATH = ROOT / "scripts" / "read_relevant.py"
READER_VALIDATOR_PATH = ROOT / "scripts" / "validate_read_relevant.py"

REQUIRED_POLICY_PHRASES = [
    "use `scripts/read_relevant.py` before full-file reads",
    "large Markdown",
    "outline",
    "section",
    "find",
    "slice",
]


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_lower(path: Path) -> str:
    return path.read_text(encoding="utf-8").lower()


def main() -> None:
    for path in [AGENTS_PATH, COMMANDS_PATH, POLICY_PATH, READER_PATH, READER_VALIDATOR_PATH]:
        assert_condition(path.is_file(), f"Required context-reading file is missing: {path.relative_to(ROOT)}")

    agents_text = read_lower(AGENTS_PATH)
    policy_text = read_lower(POLICY_PATH)
    commands_text = read_lower(COMMANDS_PATH)

    for phrase in REQUIRED_POLICY_PHRASES:
        assert_condition(phrase.lower() in agents_text, f"AGENTS.md must include context-reading phrase: {phrase}")
        assert_condition(phrase.lower() in policy_text, f"Context reading policy must include phrase: {phrase}")

    assert_condition(
        "python scripts\\read_relevant.py" in commands_text,
        "COMMANDS.md must document the project-local relevant-reader command.",
    )
    assert_condition(
        "python scripts\\validate_context_reading_policy.py" in commands_text,
        "COMMANDS.md must document context-reading policy validation.",
    )

    print("Context reading policy validation passed.")


if __name__ == "__main__":
    main()
