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
REGISTRY_PATH = ROOT / "research" / "experiments" / "generated" / "RAG-017-runtime-knowledge-registry" / "result.json"
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
        "preis" in safe_payload["final_response"].lower()
        or "aufwand" in safe_payload["final_response"].lower(),
        "Safe German response should contextually address the price concern.",
    )
    assert_condition(safe_payload["decision_snapshot"]["response_language"] == "de", "Safe response should preserve German language.")
    assert_condition(safe_payload["retrieval"]["enabled"] is False, "Retrieval must stay disabled by default.")
    assert_condition(safe_payload["retrieval"]["retrieval_used_in_runtime"] is False, "Default run must not use retrieval.")
    assert_condition(RESULT_PATH.exists(), "Expected generated JSON result file.")
    assert_condition(REPORT_PATH.exists(), "Expected generated Markdown report file.")

    rag016b_run = run_command(
        [
            PYTHON,
            str(ROOT / "scripts" / "run_rag_016b_voice_delivery_decision_slice.py"),
        ]
    )
    assert_condition(rag016b_run.returncode == 0, rag016b_run.stderr)

    registry_run = run_command(
        [
            PYTHON,
            str(ROOT / "scripts" / "run_rag_017_runtime_knowledge_registry.py"),
            "--out",
            str(REGISTRY_PATH),
        ]
    )
    assert_condition(registry_run.returncode == 0, registry_run.stderr)

    retrieval_run = run_command(
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
            "--retrieval-enabled",
            "--retrieval-registry",
            str(REGISTRY_PATH),
            "--retrieval-max-results",
            "4",
        ]
    )
    assert_condition(retrieval_run.returncode == 0, retrieval_run.stderr)
    retrieval_payload = parse_stdout_json(retrieval_run)
    retrieval = retrieval_payload["retrieval"]
    assert_condition(retrieval["enabled"] is True, retrieval)
    assert_condition(retrieval["status"] == "influenced", retrieval)
    assert_condition(retrieval["retrieval_used_in_runtime"] is True, retrieval)
    assert_condition(retrieval["blocked_reason"] == "", retrieval)
    assert_condition(retrieval["retrieved_item_ids"], retrieval)
    assert_condition(retrieval["citation_trace"], retrieval)
    assert_condition(retrieval["influenced_response"] is True, retrieval)
    assert_condition("rag016a-response-autonomy-reminder" in retrieval["retrieved_item_ids"], retrieval)
    assert_condition(retrieval_payload["validation"]["passed"] is True, retrieval_payload["validation"])
    assert_condition("source_excerpt" not in json.dumps(retrieval_payload).lower(), "Retrieval output must not include source excerpts.")
    assert_condition("data/private" not in json.dumps(retrieval_payload).replace("\\", "/").lower(), "Retrieval output must not mention private data paths.")

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

    blocked_retrieval_cases = [
        (
            "do-not-call",
            "Bitte rufen Sie mich nicht mehr an.",
            "do_not_call_overrides_retrieval",
        ),
        (
            "human-request",
            "Ich moechte mit einem Menschen sprechen.",
            "human_escalation_overrides_retrieval",
        ),
    ]
    for stage, transcript, expected_block in blocked_retrieval_cases:
        blocked_run = run_command(
            [
                PYTHON,
                str(SCRIPT),
                "--campaign",
                "campaign-prod-005-b2c-telecom",
                "--stage",
                "relevance-check",
                "--transcript",
                transcript,
                "--cases",
                str(CASES_PATH),
                "--retrieval-enabled",
                "--retrieval-registry",
                str(REGISTRY_PATH),
            ]
        )
        assert_condition(blocked_run.returncode == 0, blocked_run.stderr)
        blocked_payload = parse_stdout_json(blocked_run)
        blocked = blocked_payload["retrieval"]
        assert_condition(blocked["enabled"] is True, blocked)
        assert_condition(blocked["status"] == "blocked", blocked)
        assert_condition(blocked["blocked_reason"] == expected_block, blocked)
        assert_condition(blocked["retrieval_used_in_runtime"] is False, blocked)
        assert_condition(blocked["influenced_response"] is False, blocked)
        assert_condition(blocked["retrieved_item_ids"] == [], blocked)

    hidden_claim_run = run_command(
        [
            PYTHON,
            str(SCRIPT),
            "--campaign",
            "campaign-prod-005-b2c-telecom",
            "--stage",
            "relevance-check",
            "--transcript",
            "You sound hesitant but I may be interested if this stays simple.",
            "--cases",
            str(CASES_PATH),
            "--retrieval-enabled",
            "--retrieval-registry",
            str(REGISTRY_PATH),
        ]
    )
    assert_condition(hidden_claim_run.returncode == 0, hidden_claim_run.stderr)
    hidden_claim_payload = parse_stdout_json(hidden_claim_run)
    output_text = json.dumps(hidden_claim_payload).lower()
    forbidden_emotion_claims = [
        "you are anxious",
        "you are angry",
        "you feel afraid",
        "i can tell you feel",
    ]
    for phrase in forbidden_emotion_claims:
        assert_condition(phrase not in output_text, f"Hidden-emotion claim leaked: {phrase}")

    report_text = REPORT_PATH.read_text(encoding="utf-8")
    assert_condition("No LLM/API call was made" in report_text, "Report must state no LLM/API call was made.")
    assert_condition("fallback" in report_text.lower(), "Report must document fallback behavior.")

    assert_no_secret_text(safe_run.stdout + unsafe_run.stdout + report_text, "RESP-001 outputs")
    print("RESP-001 guarded response generation validation passed.")


if __name__ == "__main__":
    main()
