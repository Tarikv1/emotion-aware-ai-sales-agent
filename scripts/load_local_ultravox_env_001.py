#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / "runtime" / "config" / "local" / "ultravox.env"
ENABLE_GATE = "ENABLE_ULTRAVOX_SANDBOX"
ALLOW_GATE = "LOCAL_ULTRAVOX_ALLOW_PROVIDER_CALLS"
API_KEY_ENV = "ULTRAVOX_API_KEY"


class UnsafeUltravoxEnvFile(RuntimeError):
    pass


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def _is_ignored_by_git(path: Path) -> bool:
    completed = subprocess.run(
        ["git", "check-ignore", "-v", _rel(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.returncode == 0


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key:
            values[key] = value
    return values


def get_ultravox_env_metadata(*, env_file_loaded: bool = False, env_file_ignored_by_git: bool | None = None) -> dict[str, bool]:
    env_file_exists = ENV_PATH.is_file()
    ignored = _is_ignored_by_git(ENV_PATH) if env_file_ignored_by_git is None and env_file_exists else bool(env_file_ignored_by_git)
    return {
        "env_file_exists": env_file_exists,
        "env_file_ignored_by_git": ignored,
        "env_file_loaded": env_file_loaded,
        "api_key_present": bool(os.environ.get(API_KEY_ENV)),
        "gates_enabled": (
            os.environ.get(ENABLE_GATE) == "1"
            and os.environ.get(ALLOW_GATE) == "1"
            and bool(os.environ.get(API_KEY_ENV))
        ),
    }


def load_local_ultravox_env() -> dict[str, bool]:
    if not ENV_PATH.exists():
        return get_ultravox_env_metadata(env_file_loaded=False, env_file_ignored_by_git=False)

    ignored = _is_ignored_by_git(ENV_PATH)
    if not ignored:
        raise UnsafeUltravoxEnvFile("runtime/config/local/ultravox.env exists but is not ignored by Git")

    loaded_values = _parse_env_file(ENV_PATH)
    for key, value in loaded_values.items():
        if os.environ.get(key) is None:
            os.environ[key] = value
    return get_ultravox_env_metadata(env_file_loaded=True, env_file_ignored_by_git=True)


def build_safe_metadata() -> dict[str, Any]:
    return load_local_ultravox_env()
