#!/usr/bin/env python3
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "read_relevant.py"
COMMANDS_PATH = "docs/product/COMMANDS.md"
SECRET_VALUE = "TEST_OPENAI_VALUE_MUST_NOT_APPEAR"


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_reader(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["OPENAI_API_KEY"] = SECRET_VALUE
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=check,
    )


def load_json(*args: str) -> dict:
    completed = run_reader(*args, "--json")
    combined = completed.stdout + completed.stderr
    assert_condition(SECRET_VALUE not in combined, "Reader leaked an environment value.")
    payload = json.loads(completed.stdout)
    assert_condition(payload["summary"]["network_calls_made"] is False, "Reader must not make network calls.")
    assert_condition(payload["summary"]["secret_values_logged"] is False, "Reader must not log secret values.")
    return payload


def main() -> None:
    assert_condition(SCRIPT_PATH.exists(), "Product-local relevant reader is missing.")

    outline = load_json("outline", "--path", COMMANDS_PATH)
    assert_condition(outline["path"] == COMMANDS_PATH, "Unexpected outline path.")
    assert_condition("text" not in outline, "Outline should not include full file text.")
    assert_condition(any(heading["title"] == "Setup" for heading in outline["headings"]), "Setup heading missing.")

    slice_payload = load_json("slice", "--path", COMMANDS_PATH, "--start", "11", "--end", "17")
    assert_condition(slice_payload["start"] == 11, "Unexpected slice start.")
    assert_condition(slice_payload["end"] == 17, "Unexpected slice end.")
    assert_condition("python scripts\\check_setup.py" in slice_payload["text"], "Setup command missing from slice.")
    assert_condition("Cartesia" not in slice_payload["text"], "Slice returned unrelated later content.")

    find_payload = load_json("find", "--path", COMMANDS_PATH, "--query", "Cartesia", "--context", "1")
    assert_condition(find_payload["matches"], "Expected Cartesia matches.")
    assert_condition(find_payload["matches"][0]["line"] > 0, "Find result should include line numbers.")

    section_payload = load_json("section", "--path", COMMANDS_PATH, "--heading", "Setup")
    assert_condition(section_payload["heading"] == "Setup", "Unexpected section heading.")
    assert_condition("python scripts\\check_setup.py" in section_payload["text"], "Section missing setup command.")
    assert_condition("Core Product Contract" not in section_payload["text"], "Section crossed into next heading.")

    blocked = run_reader("slice", "--path", ".git/config", "--start", "1", "--end", "2", check=False)
    assert_condition(blocked.returncode != 0, "Blocked path read should fail.")
    assert_condition("Blocked path" in (blocked.stdout + blocked.stderr), "Blocked path failure should be explicit.")

    print("Product-local relevant reader validation passed.")


if __name__ == "__main__":
    main()
