#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LOADER_PATH = ROOT / "scripts" / "load_local_ultravox_env_001.py"
ENV_PATH = ROOT / "runtime" / "config" / "local" / "ultravox.env"
GENERATED_ROOT = ROOT / "research" / "experiments" / "generated"

SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|ULTRAVOX_API_KEY\s*=\s*(?!\.\.\.|<redacted>|your-api-key)[^\s]+|Authorization:\s*Bearer\s+[A-Za-z0-9]|X-API-Key:\s*(?!<redacted>|your-api-key)[A-Za-z0-9])"
)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def fail(message: str) -> None:
    raise AssertionError(message)


def git_ignored(path: Path) -> bool:
    completed = subprocess.run(
        ["git", "check-ignore", "-v", rel(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.returncode == 0


def load_loader_module() -> Any:
    if not LOADER_PATH.is_file():
        fail(f"missing loader: {rel(LOADER_PATH)}")
    text = LOADER_PATH.read_text(encoding="utf-8")
    if "print(" in text:
        fail("env loader must not print environment or secret metadata directly")
    spec = importlib.util.spec_from_file_location("load_local_ultravox_env_001_under_test", LOADER_PATH)
    if spec is None or spec.loader is None:
        fail("could not import local Ultravox env loader")
    module = importlib.util.module_from_spec(spec)
    sys.modules["load_local_ultravox_env_001_under_test"] = module
    spec.loader.exec_module(module)
    return module


def assert_no_secret_patterns(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    match = SECRET_PATTERN.search(text)
    if match:
        fail(f"secret-like token found in {rel(path)}: {match.group(0)!r}")


def assert_generated_evidence_has_no_secrets() -> None:
    if not GENERATED_ROOT.exists():
        return
    for path in GENERATED_ROOT.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".json", ".md", ".txt"}:
            assert_no_secret_patterns(path)


def main() -> None:
    if ENV_PATH.exists() and not git_ignored(ENV_PATH):
        fail("runtime/config/local/ultravox.env exists but is not ignored by Git")

    loader = load_loader_module()
    if not callable(getattr(loader, "load_local_ultravox_env", None)):
        fail("loader missing callable: load_local_ultravox_env")
    if not callable(getattr(loader, "get_ultravox_env_metadata", None)):
        fail("loader missing callable: get_ultravox_env_metadata")

    before = dict(os.environ)
    metadata = loader.load_local_ultravox_env()
    for key, value in before.items():
        os.environ[key] = value
    for key in set(os.environ) - set(before):
        os.environ.pop(key, None)

    for key in ("env_file_exists", "env_file_ignored_by_git", "env_file_loaded", "api_key_present", "gates_enabled"):
        if key not in metadata or not isinstance(metadata[key], bool):
            fail(f"metadata missing boolean field: {key}")
    if metadata["env_file_exists"] and metadata["env_file_ignored_by_git"] is not True:
        fail("env file exists but loader did not verify Git ignore status")
    if "api_key_value" in metadata or "ULTRAVOX_API_KEY" in json.dumps(metadata):
        fail("loader metadata must not expose the API key or key name as a value field")

    tracked = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.splitlines()
    for relative in tracked:
        path = ROOT / relative
        if path.is_file() and path.suffix.lower() in {".py", ".json", ".md", ".txt", ".env"}:
            assert_no_secret_patterns(path)
    assert_generated_evidence_has_no_secrets()
    print("Local Ultravox env validation passed.")


if __name__ == "__main__":
    main()
