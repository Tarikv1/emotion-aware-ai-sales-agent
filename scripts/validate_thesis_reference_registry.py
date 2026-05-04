#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "check_thesis_reference_registry.py"
FIXTURE_ROOT = ROOT / ".tmp" / "thesis-reference-registry-validation" / f"run-{uuid.uuid4().hex}"


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def create_fixture(root: Path, registered: bool) -> None:
    registry_url = "https://" + "research.example.test/source"
    unregistered_url = "https://" + "missing-source.example.test/article"
    registry_text = f"# Thesis Reference Registry\n\n- Registered: {registry_url}\n"
    inspiration_text = "# Third-Party Inspirations\n\nNo runtime dependencies.\n"
    if registered:
        registry_text += f"- Also registered: {unregistered_url}\n"

    write_text(root / "docs" / "thesis" / "THESIS_REFERENCE_REGISTRY.md", registry_text)
    write_text(root / "docs" / "thesis" / "SPEECH_REALISM_REFERENCES.md", "# Speech Realism References\n\nFixture reference companion.\n")
    write_text(root / "docs" / "third-party-inspirations.md", inspiration_text)
    write_text(root / "docs" / "product" / "registered.md", f"Uses {registry_url} as a cited source.\n")
    write_text(root / "docs" / "product" / "local-demo.md", "Demo URL: http://127.0.0.1:8765\n")
    write_text(root / "research" / "experiments" / "source-note.md", f"Needs registry coverage: {unregistered_url}\n")


def run_guard(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--root", str(root), "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )


def parse_json_output(completed: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Guard did not return valid JSON. stdout={completed.stdout!r} stderr={completed.stderr!r}") from exc


def validate_dirty_fixture() -> None:
    dirty_root = FIXTURE_ROOT / "dirty"
    create_fixture(dirty_root, registered=False)

    completed = run_guard(dirty_root)
    assert_condition(completed.returncode != 0, "Dirty fixture should fail when a URL is not in the registry.")
    payload = parse_json_output(completed)
    assert_condition(payload["status"] == "fail", "Dirty fixture payload should fail.")
    issue_codes = {issue["code"] for issue in payload["issues"]}
    assert_condition("unregistered_external_reference" in issue_codes, "Missing URL issue was not reported.")
    assert_condition(payload["summary"]["network_calls_made"] is False, "Guard must not make network calls.")
    assert_condition(payload["summary"]["auto_fixes_applied"] is False, "Guard must not auto-fix references.")


def validate_clean_fixture() -> None:
    clean_root = FIXTURE_ROOT / "clean"
    create_fixture(clean_root, registered=True)

    completed = run_guard(clean_root)
    assert_condition(completed.returncode == 0, f"Clean fixture should pass. stdout={completed.stdout!r}")
    payload = parse_json_output(completed)
    assert_condition(payload["status"] == "pass", "Clean fixture payload should pass.")
    assert_condition(payload["summary"]["failure_count"] == 0, "Clean fixture should have no failures.")
    assert_condition(payload["summary"]["network_calls_made"] is False, "Guard must not make network calls.")
    assert_condition(payload["summary"]["auto_fixes_applied"] is False, "Guard must not auto-fix references.")


def validate_current_repo() -> None:
    completed = run_guard(ROOT)
    assert_condition(completed.returncode == 0, f"Current repo should pass reference registry guard. stdout={completed.stdout!r}")
    payload = parse_json_output(completed)
    assert_condition(payload["project"] == "emotion-aware-ai-sales-agent", "Unexpected project name.")
    assert_condition(payload["status"] == "pass", "Current repo reference registry status should pass.")


def main() -> None:
    assert_condition(SCRIPT_PATH.exists(), "Thesis reference registry guard is missing.")
    FIXTURE_ROOT.mkdir(parents=True, exist_ok=True)

    try:
        validate_dirty_fixture()
        validate_clean_fixture()
        validate_current_repo()
    finally:
        shutil.rmtree(FIXTURE_ROOT, ignore_errors=True)

    print("Thesis reference registry guard validation passed.")


if __name__ == "__main__":
    main()
