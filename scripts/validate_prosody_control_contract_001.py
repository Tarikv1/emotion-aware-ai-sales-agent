#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.audio_backends.prosody_control_contract import PROSODY_OBJECT_FIELDS, STANDARD_VALUES

CONTRACT_PATH = ROOT / "runtime" / "audio_backends" / "prosody_control_contract.py"
POLICY_PATH = ROOT / "runtime" / "audio_backends" / "prosody_style_policy.json"
FISH_TAGS = ("[pause]", "[emphasis]", "[calm]", "[whispering]", "[reassuring]")
LIVE_RUNTIME_PREFIXES = (
    "runtime/core/",
    "runtime/entrypoints/",
    "runtime/providers/",
    "runtime/speech/",
    "runtime/voice/",
)
LIVE_RUNTIME_SCRIPT_FILES = (
    "scripts/runtime_voice_delivery.py",
    "scripts/runtime_tts_delivery.py",
    "scripts/tts_provider_clients.py",
    "scripts/generate_runtime_voice_delivery.py",
    "scripts/generate_runtime_tts_delivery.py",
    "scripts/run_resp_003_runtime_live_tts.py",
)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise AssertionError(f"missing file: {rel(path)}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError(f"{rel(path)} must be a JSON object")
    return payload


def git_lines(args: list[str]) -> list[str]:
    completed = subprocess.run(
        ["git", "--no-optional-locks", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if completed.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()]


def live_runtime_tag_hits() -> list[str]:
    hits: list[str] = []
    for path in git_lines(["ls-files"]):
        if not (path.startswith(LIVE_RUNTIME_PREFIXES) or path in LIVE_RUNTIME_SCRIPT_FILES):
            continue
        file_path = ROOT / path
        if file_path.suffix not in {".py", ".json", ".md", ".txt"}:
            continue
        text = file_path.read_text(encoding="utf-8", errors="replace")
        for tag in FISH_TAGS:
            if tag in text:
                hits.append(f"{path}:{tag}")
    return hits


def changed_live_runtime_files() -> list[str]:
    changed = git_lines(["diff", "--name-only", "HEAD"])
    return [
        path
        for path in changed
        if path.startswith(("runtime/core/", "runtime/entrypoints/", "runtime/providers/", "runtime/speech/", "runtime/voice/"))
    ]


def main() -> int:
    failures: list[str] = []
    if not CONTRACT_PATH.is_file():
        failures.append(f"missing contract: {rel(CONTRACT_PATH)}")
    policy = load_json(POLICY_PATH)

    template = policy.get("prosody_object_template") if isinstance(policy.get("prosody_object_template"), dict) else {}
    missing_fields = sorted(set(PROSODY_OBJECT_FIELDS) - set(template))
    if missing_fields:
        failures.append(f"prosody template missing fields: {missing_fields}")

    standard_values = policy.get("standard_values") if isinstance(policy.get("standard_values"), dict) else {}
    for key, expected_values in STANDARD_VALUES.items():
        actual = tuple(standard_values.get(key) or ())
        if actual != expected_values:
            failures.append(f"standard_values.{key} mismatch")

    mappings = policy.get("backend_mappings") if isinstance(policy.get("backend_mappings"), dict) else {}
    for required_mapping in ("elevenlabs_existing_provider", "kokoro_82m", "fish_audio_s2_inspired", "liquid_audio_lfm25"):
        if required_mapping not in mappings:
            failures.append(f"missing backend mapping: {required_mapping}")
    fish_mapping = mappings.get("fish_audio_s2_inspired", {}) if isinstance(mappings.get("fish_audio_s2_inspired"), dict) else {}
    if fish_mapping.get("runtime_status") != "inspiration_only_not_active_runtime":
        failures.append("Fish-inspired mapping must be inspiration-only")
    if fish_mapping.get("allowed_now") is not False:
        failures.append("Fish-inspired mapping must not be allowed now")

    flags = policy.get("runtime_boundaries") if isinstance(policy.get("runtime_boundaries"), dict) else {}
    for key in (
        "live_runtime_allowed",
        "inject_fish_tags_into_live_elevenlabs",
        "alter_current_live_spoken_responses",
        "provider_calls_made",
        "live_tts_calls_made",
        "runtime_behavior_changed",
        "response_text_changed",
    ):
        if flags.get(key) is not False:
            failures.append(f"runtime_boundaries.{key} must be false")

    tag_hits = live_runtime_tag_hits()
    if tag_hits:
        failures.append(f"Fish-inspired tags are wired into live runtime files: {tag_hits[:20]}")

    live_changes = changed_live_runtime_files()
    if live_changes:
        failures.append(f"live runtime files changed: {live_changes}")

    result = {
        "status": "pass" if not failures else "fail",
        "contract": rel(CONTRACT_PATH),
        "policy": rel(POLICY_PATH),
        "fish_tag_hits": tag_hits,
        "failures": failures,
        "provider_calls_made": False,
        "live_tts_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False
    }
    print(json.dumps(result, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
