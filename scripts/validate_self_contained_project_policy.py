#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DOCS = [
    ROOT / "docs" / "product" / "PROJECT_SELF_CONTAINMENT_POLICY.md",
    ROOT / "docs" / "product" / "VOICE_PROVIDER_RUN_BOUNDARY.md",
    ROOT / "docs" / "product" / "VOICE_GENERATED_AUDIO_ASSET_LOG.md",
]

FORBIDDEN_SCRIPT_REFERENCES = [
    "D:\\Codex\\shared",
    "D:/Codex/shared",
    "..\\..\\shared",
    "../../shared",
    "active\\youtube-channel",
    "active/youtube-channel",
    "active\\client-websites",
    "active/client-websites",
    "active\\codex-workspace-dashboard",
    "active/codex-workspace-dashboard",
]

REQUIRED_BOUNDARY_PHRASES = [
    "environment-only",
    "no customer audio",
    "no voice cloning",
    "bounded timeout",
    "explicit opt-in",
]

REQUIRED_ASSET_LOG_FIELDS = [
    "provider",
    "output path",
    "network used",
    "upload used",
    "api key location",
    "synthetic prompt",
    "customer audio uploaded",
    "voice cloning used",
    "human listening review",
]


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_lower(path: Path) -> str:
    return path.read_text(encoding="utf-8").lower()


def validate_docs_exist() -> None:
    for path in REQUIRED_DOCS:
        assert_condition(path.is_file(), f"Required self-contained project doc is missing: {path.relative_to(ROOT)}")


def validate_boundary_doc() -> None:
    text = read_lower(ROOT / "docs" / "product" / "VOICE_PROVIDER_RUN_BOUNDARY.md")
    for phrase in REQUIRED_BOUNDARY_PHRASES:
        assert_condition(phrase in text, f"Provider boundary doc must include phrase: {phrase}")


def validate_asset_log_doc() -> None:
    text = read_lower(ROOT / "docs" / "product" / "VOICE_GENERATED_AUDIO_ASSET_LOG.md")
    for field in REQUIRED_ASSET_LOG_FIELDS:
        assert_condition(field in text, f"Generated audio asset log doc must include field: {field}")


def validate_scripts_are_project_local() -> None:
    violations = []
    for path in (ROOT / "scripts").glob("*.py"):
        if path.name == Path(__file__).name:
            continue
        text = path.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_SCRIPT_REFERENCES:
            if forbidden in text:
                violations.append(f"{path.relative_to(ROOT)} references external workspace path {forbidden!r}")
    assert_condition(not violations, "Project scripts must be self-contained:\n" + "\n".join(violations))


def main() -> None:
    validate_docs_exist()
    validate_boundary_doc()
    validate_asset_log_doc()
    validate_scripts_are_project_local()
    print("Self-contained project policy validation passed.")


if __name__ == "__main__":
    main()
