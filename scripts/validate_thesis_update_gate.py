#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "check_thesis_update_gate.py"
COMMANDS_PATH = ROOT / "docs" / "product" / "COMMANDS.md"
WRITING_GUIDE_PATH = ROOT / "docs" / "thesis" / "THESIS_WRITING_GUIDE.md"
REVIEW_GATES_PATH = ROOT / "docs" / "product-review-gates.md"
FIXTURE_RUNTIME_SCRIPT = "scripts/" + "new_runtime_feature.py"
FIXTURE_RUNTIME_DOC = "docs/" + "product/" + "NEW_RUNTIME_FEATURE.md"


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_gate(*changed_files: str) -> subprocess.CompletedProcess[str]:
    args = [sys.executable, str(SCRIPT_PATH), "--json"]
    for changed_file in changed_files:
        args.extend(["--changed-file", changed_file])
    return subprocess.run(
        args,
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
        raise AssertionError(f"Gate did not return valid JSON. stdout={completed.stdout!r} stderr={completed.stderr!r}") from exc


def validate_missing_thesis_update() -> None:
    completed = run_gate(FIXTURE_RUNTIME_SCRIPT, FIXTURE_RUNTIME_DOC)
    assert_condition(completed.returncode != 0, "Product/runtime changes without thesis docs should fail.")
    payload = parse_json_output(completed)
    assert_condition(payload["status"] == "fail", "Missing thesis update payload should fail.")
    issue_codes = {issue["code"] for issue in payload["issues"]}
    assert_condition("missing_thesis_update" in issue_codes, "Missing thesis update issue was not reported.")
    assert_condition(payload["summary"]["auto_fixes_applied"] is False, "Gate must not auto-fix docs.")


def validate_with_thesis_update() -> None:
    completed = run_gate(
        FIXTURE_RUNTIME_SCRIPT,
        FIXTURE_RUNTIME_DOC,
        "docs/thesis/METHODOLOGY_LOG.md",
    )
    assert_condition(completed.returncode == 0, f"Product changes with thesis docs should pass. stdout={completed.stdout!r}")
    payload = parse_json_output(completed)
    assert_condition(payload["status"] == "pass", "Thesis-documented change should pass.")
    assert_condition(payload["summary"]["failure_count"] == 0, "Thesis-documented change should have no failures.")


def validate_thesis_only_change() -> None:
    completed = run_gate("docs/thesis/ROADMAP.md")
    assert_condition(completed.returncode == 0, f"Thesis-only changes should pass. stdout={completed.stdout!r}")
    payload = parse_json_output(completed)
    assert_condition(payload["status"] == "pass", "Thesis-only payload should pass.")


def validate_current_repo() -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert_condition(completed.returncode == 0, f"Current repo should pass thesis update gate. stdout={completed.stdout!r}")
    payload = parse_json_output(completed)
    assert_condition(payload["project"] == "emotion-aware-ai-sales-agent", "Unexpected project name.")
    assert_condition(payload["status"] == "pass", "Current repo thesis update gate status should pass.")


def validate_docs() -> None:
    for path in [COMMANDS_PATH, WRITING_GUIDE_PATH, REVIEW_GATES_PATH]:
        assert_condition(path.is_file(), f"Required thesis gate doc is missing: {path.relative_to(ROOT)}")

    commands_text = COMMANDS_PATH.read_text(encoding="utf-8")
    guide_text = WRITING_GUIDE_PATH.read_text(encoding="utf-8")
    gates_text = REVIEW_GATES_PATH.read_text(encoding="utf-8")

    assert_condition(
        "python scripts\\check_thesis_reference_registry.py" in commands_text,
        "COMMANDS.md must document the thesis reference registry guard.",
    )
    assert_condition(
        "python scripts\\check_thesis_update_gate.py" in commands_text,
        "COMMANDS.md must document the thesis update gate.",
    )
    assert_condition(
        "pre-push thesis traceability gate" in guide_text.lower(),
        "THESIS_WRITING_GUIDE.md must describe the pre-push thesis traceability gate.",
    )
    assert_condition(
        "check_thesis_update_gate.py" in gates_text,
        "Product review gates must mention the thesis update gate.",
    )


def main() -> None:
    assert_condition(SCRIPT_PATH.exists(), "Thesis update gate is missing.")
    validate_missing_thesis_update()
    validate_with_thesis_update()
    validate_thesis_only_change()
    validate_current_repo()
    validate_docs()
    print("Thesis update gate validation passed.")


if __name__ == "__main__":
    main()
