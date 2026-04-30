#!/usr/bin/env python3
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_guarded_response.py"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "RESP-001-guarded-response-result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "RESP-001-guarded-response-report.md"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "prod-005-realtime-latency-call-control.json"
PYTHON = sys.executable


SECRET_PATTERN = re.compile(
    r"\b(sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{20,}|xox[baprs]-[A-Za-z0-9-]{20,})\b"
)


def run_command(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True)


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def parse_stdout_json(completed: subprocess.CompletedProcess) -> dict:
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Expected JSON stdout, got: {completed.stdout!r}") from exc


def assert_no_secret_text(text: str, label: str) -> None:
    match = SECRET_PATTERN.search(text)
    if match is not None:
        raise AssertionError(f"Potential secret-like value found in {label}: {match.group(0)!r}")


def main() -> None:
    assert_condition(SCRIPT.exists(), "RESP-001 generator script is missing.")

    safe_transcript = "Das klingt zu teuer und ich weiss nicht, ob sich der Aufwand lohnt."
    safe_run = run_command(
        [
            PYTHON,
            str(SCRIPT),
            "--campaign",
            "campaign-prod-005-b2c-telecom",
            "--stage",
            "relevance-check",
            "--transcript",
            safe_transcript,
            "--cases",
            str(CASES_PATH),
            "--out",
            str(RESULT_PATH),
            "--report-out",
            str(REPORT_PATH),
        ]
    )
    assert_condition(safe_run.returncode == 0, safe_run.stderr)
    safe_payload = parse_stdout_json(safe_run)

    assert_condition(safe_payload["response_generation_id"] == "RESP-001-local-guarded", "Unexpected response ID.")
    assert_condition(safe_payload["provider"] == "local-guarded-composer", "Unexpected provider.")
    assert_condition(safe_payload["llm_used"] is False, "RESP-001 must not call an LLM yet.")
    assert_condition(safe_payload["requires_api_key"] is False, "RESP-001 must not require an API key.")
    assert_condition(
        safe_payload["decision_snapshot"]["sales_difficulty"] == "price-objection",
        "Safe sample should classify as a price objection.",
    )
    assert_condition(safe_payload["validation"]["passed"] is True, "Safe response should pass validation.")
    assert_condition(safe_payload["validation"]["fallback_used"] is False, "Safe response should not use fallback.")
    assert_condition(
        safe_payload["final_response"] != safe_payload["policy_response"],
        "Safe response should improve wording beyond the policy fallback.",
    )
    assert_condition(
        "monthly price" in safe_payload["final_response"].lower()
        or "price" in safe_payload["final_response"].lower()
        or "cost" in safe_payload["final_response"].lower(),
        "Safe response should contextually address the price concern.",
    )
    assert_condition(RESULT_PATH.exists(), "Expected generated JSON result file.")
    assert_condition(REPORT_PATH.exists(), "Expected generated Markdown report file.")

    unsafe_run = run_command(
        [
            PYTHON,
            str(SCRIPT),
            "--campaign",
            "campaign-prod-005-b2c-telecom",
            "--stage",
            "relevance-check",
            "--transcript",
            safe_transcript,
            "--cases",
            str(CASES_PATH),
            "--candidate-response",
            "I guarantee this will save you money and always be stable.",
        ]
    )
    assert_condition(unsafe_run.returncode == 0, unsafe_run.stderr)
    unsafe_payload = parse_stdout_json(unsafe_run)
    forbidden_matches = unsafe_payload["validation"]["forbidden_claim_matches"]

    assert_condition(unsafe_payload["validation"]["passed"] is False, "Unsafe candidate must fail validation.")
    assert_condition(unsafe_payload["validation"]["fallback_used"] is True, "Unsafe candidate must use fallback.")
    assert_condition(
        unsafe_payload["final_response"] == unsafe_payload["policy_response"],
        "Unsafe candidate should be replaced by policy fallback.",
    )
    assert_condition(any("guarantee" in item for item in forbidden_matches), "Guarantee claim should be detected.")
    assert_condition(any("save you money" in item for item in forbidden_matches), "Savings claim should be detected.")
    assert_condition(any("always be stable" in item for item in forbidden_matches), "Stability claim should be detected.")
    assert_condition("save you money" not in unsafe_payload["final_response"].lower(), "Fallback must remove savings claim.")
    assert_condition("always be stable" not in unsafe_payload["final_response"].lower(), "Fallback must remove stability claim.")

    report_text = REPORT_PATH.read_text(encoding="utf-8")
    assert_condition("No LLM/API call was made" in report_text, "Report must state no LLM/API call was made.")
    assert_condition("fallback" in report_text.lower(), "Report must document fallback behavior.")

    assert_no_secret_text(safe_run.stdout + unsafe_run.stdout + report_text, "RESP-001 outputs")
    print("RESP-001 guarded response generation validation passed.")


if __name__ == "__main__":
    main()
