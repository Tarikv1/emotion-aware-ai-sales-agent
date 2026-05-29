#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-DASHBOARD-VS-API-NOTE-001" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-DASHBOARD-VS-API-NOTE-001" / "report.md"

SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|u[a-z]?v[A-Za-z0-9_-]{20,}|ULTRAVOX_API_KEY\s*=\s*[^\s]+|Authorization:\s*Bearer\s+[A-Za-z0-9]|X-API-Key:\s*[A-Za-z0-9])"
)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def fail(message: str) -> None:
    raise AssertionError(message)


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        fail(f"missing file: {rel(path)}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        fail(f"{rel(path)} must be a JSON object")
    return payload


def assert_no_secret_patterns(text: str) -> None:
    match = SECRET_PATTERN.search(text)
    if match:
        fail(f"secret-like token found: {match.group(0)!r}")


def main() -> None:
    result = load_json(RESULT_PATH)
    report_text = REPORT_PATH.read_text(encoding="utf-8") if REPORT_PATH.is_file() else ""
    if not report_text:
        fail(f"missing file: {rel(REPORT_PATH)}")
    assert_no_secret_patterns(json.dumps(result) + report_text)

    if result.get("evaluation_id") != "ULTRAVOX-DASHBOARD-VS-API-NOTE-001":
        fail("unexpected dashboard/API note evaluation_id")
    if result.get("manual_dashboard_upload_performed") is not False:
        fail("dashboard note must record no manual dashboard upload")
    if result.get("secrets_recorded") is not False:
        fail("dashboard note must record no secrets")
    if result.get("api_script_path_used_first") is not True:
        fail("dashboard note must prefer API/script path first")
    waits = result.get("durable_dashboard_setup_waits_for", [])
    required = {
        "tool schema is stable",
        "public HTTPS tool endpoint or client-tool strategy is decided",
        "secret handling is confirmed",
        "synthetic sandbox passes",
    }
    missing = sorted(required - set(waits))
    if missing:
        fail(f"dashboard note missing wait condition(s): {missing}")
    if "Dashboard may be useful later" not in report_text:
        fail("dashboard report missing summary")
    print("ULTRAVOX dashboard/API note validation passed.")


if __name__ == "__main__":
    main()
