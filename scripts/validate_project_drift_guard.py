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
SCRIPT_PATH = ROOT / "scripts" / "check_project_drift.py"
FIXTURE_ROOT = ROOT / ".tmp" / "project-drift-validation" / f"run-{uuid.uuid4().hex}"

REQUIRED_FIXTURE_FILES = [
    "AGENTS.md",
    "README.md",
    "docs/product/CONTEXT_READING_POLICY.md",
    "docs/product/PROJECT_SELF_CONTAINMENT_POLICY.md",
    "docs/product/VOICE_PROVIDER_RUN_BOUNDARY.md",
    "docs/product/VOICE_GENERATED_AUDIO_ASSET_LOG.md",
    "docs/product/PROJECT_DRIFT_GUARD.md",
    "docs/product/COMMANDS.md",
    "docs/product-review-gates.md",
    "docs/third-party-inspirations.md",
    "docs/data/PRIVATE_CALL_CENTER_DATA_POLICY.md",
    "docs/data/PRIVATE_CALL_LEARNING_PIPELINE.md",
    "docs/thesis/ROADMAP.md",
    "docs/thesis/METHODOLOGY_LOG.md",
    "docs/thesis/DECISION_LOG.md",
    "docs/thesis/THESIS_REFERENCE_REGISTRY.md",
    "docs/thesis/THESIS_WRITING_GUIDE.md",
    "data/private/.gitignore",
    "scripts/check_project_drift.py",
    "scripts/check_thesis_reference_registry.py",
    "scripts/validate_thesis_reference_registry.py",
    "scripts/check_thesis_update_gate.py",
    "scripts/validate_thesis_update_gate.py",
    "scripts/speech_realism.py",
    "scripts/run_voice_023_speech_realism.py",
    "scripts/validate_voice_023_speech_realism.py",
    "scripts/validate_private_data_boundary.py",
    "scripts/check_private_call_learning_pipeline.py",
    "scripts/init_private_call_learning_workspace.py",
    "scripts/validate_private_call_learning_pipeline.py",
    "scripts/validate_context_reading_policy.py",
    "scripts/validate_project_drift_guard.py",
]


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def create_base_fixture(root: Path) -> None:
    for relative_path in REQUIRED_FIXTURE_FILES:
        write_text(root / relative_path, f"# {Path(relative_path).name}\n\nFixture file.\n")
    (root / "research" / "experiments" / "generated").mkdir(parents=True, exist_ok=True)
    write_text(
        root / ".gitignore",
        "\n".join(
            [
                ".tmp/",
                "__pycache__/",
                "data/public/*",
                "data/private/*",
                "!data/private/.gitignore",
                "research/experiments/generated/*.mp3",
                "research/experiments/generated/*.wav",
                "",
            ]
        ),
    )


def create_dirty_fixture(root: Path) -> None:
    create_base_fixture(root)
    write_text(root / "README.md", "# Dirty fixture\n\n<<<<<<< HEAD\nlocal\n=======\nremote\n>>>>>>> branch\n")
    external_path = "/".join(["D:", "Codex", "shared", "templates", "voice-ai-consent-checklist.md"])
    write_text(
        root / "scripts" / "bad_external_dependency.py",
        "SOURCE = " + repr(external_path) + "\n",
    )
    fake_secret = "sk-" + "TESTVALUE" + ("X" * 24)
    write_text(root / "docs" / "bad-secret.md", f"Do not store keys like {fake_secret}.\n")
    write_text(root / ".gitignore", ".tmp/\n__pycache__/\n")
    audio_path = root / "research" / "experiments" / "generated" / "leaky-audio.mp3"
    audio_path.write_bytes(b"fixture audio bytes")


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
    create_dirty_fixture(dirty_root)

    completed = run_guard(dirty_root)
    assert_condition(completed.returncode != 0, "Dirty fixture should fail project drift guard.")
    payload = parse_json_output(completed)
    assert_condition(payload["status"] == "fail", "Dirty fixture payload should be fail.")

    issue_codes = {issue["code"] for issue in payload["issues"]}
    for expected_code in [
        "conflict_marker",
        "external_workspace_dependency",
        "secret_like_value",
        "generated_audio_not_ignored",
    ]:
        assert_condition(expected_code in issue_codes, f"Dirty fixture did not report {expected_code}.")

    assert_condition(payload["summary"]["auto_fixes_applied"] is False, "Guard must not auto-fix dirty fixture.")


def validate_clean_fixture() -> None:
    clean_root = FIXTURE_ROOT / "clean"
    create_base_fixture(clean_root)
    audio_path = clean_root / "research" / "experiments" / "generated" / "ignored-audio.mp3"
    audio_path.write_bytes(b"fixture audio bytes")

    completed = run_guard(clean_root)
    assert_condition(completed.returncode == 0, f"Clean fixture should pass. stderr={completed.stderr!r}")
    payload = parse_json_output(completed)
    assert_condition(payload["status"] == "pass", "Clean fixture payload should be pass.")
    assert_condition(payload["summary"]["failure_count"] == 0, "Clean fixture should not have failures.")
    assert_condition(payload["summary"]["auto_fixes_applied"] is False, "Guard must not auto-fix clean fixture.")


def validate_current_repo() -> None:
    completed = run_guard(ROOT)
    assert_condition(completed.returncode == 0, f"Current repo should pass project drift guard. stdout={completed.stdout!r}")
    payload = parse_json_output(completed)
    assert_condition(payload["project"] == "emotion-aware-ai-sales-agent", "Unexpected project name.")
    assert_condition(payload["status"] == "pass", "Current repo drift guard status should be pass.")
    assert_condition(payload["summary"]["auto_fixes_applied"] is False, "Guard must not auto-fix current repo.")


def main() -> None:
    assert_condition(SCRIPT_PATH.exists(), "Project drift guard runner is missing.")
    FIXTURE_ROOT.mkdir(parents=True, exist_ok=True)

    try:
        validate_dirty_fixture()
        validate_clean_fixture()
        validate_current_repo()
    finally:
        shutil.rmtree(FIXTURE_ROOT, ignore_errors=True)

    print("Project drift guard validation passed.")


if __name__ == "__main__":
    main()
