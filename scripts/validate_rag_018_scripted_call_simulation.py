#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_rag_018_scripted_call_simulation.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "rag-018-scripted-call-simulation.json"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "RAG-018-scripted-call-simulation" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "RAG-018-scripted-call-simulation" / "report.md"
DOC_PATH = ROOT / "docs" / "product" / "RAG_018_GUARDED_RUNTIME_RETRIEVAL.md"

EXPECTED_CASE_COUNT = 10
EXPECTED_INFLUENCED_COUNT = 4


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=90)


def main() -> None:
    assert_condition(RUNNER.exists(), "RAG-018 scripted-call simulation runner is missing.")
    assert_condition(CASE_PATH.exists(), "RAG-018 scripted-call simulation case file is missing.")
    assert_condition(DOC_PATH.exists(), "RAG-018 product doc is missing.")

    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--cases",
            str(CASE_PATH),
            "--out",
            str(RESULT_PATH),
            "--report-out",
            str(REPORT_PATH),
        ]
    )
    assert_condition(
        completed.returncode == 0,
        f"Simulation failed. stdout={completed.stdout!r} stderr={completed.stderr!r}",
    )
    assert_condition(RESULT_PATH.exists(), "Simulation result JSON was not written.")
    assert_condition(REPORT_PATH.exists(), "Simulation report was not written.")

    payload = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    report = REPORT_PATH.read_text(encoding="utf-8")
    summary = payload["summary"]
    cases = payload["cases"]
    combined = (json.dumps(payload, ensure_ascii=False).lower() + "\n" + report.lower()).replace("\\", "/")

    assert_condition(payload["simulation_id"] == "RAG-018-scripted-call-simulation", payload)
    assert_condition(payload["provider_calls_made"] is False, payload)
    assert_condition(payload["private_customer_data_used"] is False, payload)
    assert_condition(payload["llm_used"] is False, payload)
    assert_condition(payload["external_vector_db_used"] is False, payload)
    assert_condition(payload["embedding_provider_used"] is False, payload)
    assert_condition(summary["case_count"] == EXPECTED_CASE_COUNT, summary)
    assert_condition(summary["safe_case_count"] == EXPECTED_CASE_COUNT, summary)
    assert_condition(summary["unsafe_case_count"] == 0, summary)
    assert_condition(summary["retrieval_influenced_count"] == EXPECTED_INFLUENCED_COUNT, summary)
    assert_condition(summary["objection_resolution_improved_count"] == EXPECTED_INFLUENCED_COUNT, summary)
    assert_condition(summary["next_step_quality_improved_count"] == EXPECTED_INFLUENCED_COUNT, summary)
    assert_condition(summary["protected_context_count"] >= 4, summary)
    assert_condition(summary["protected_contexts_preserved"] == summary["protected_context_count"], summary)
    assert_condition(summary["retrieval_over_acceptable_count"] == 0, summary)
    assert_condition(payload["decision"] == "keep_rag_018_opt_in_and_do_not_make_default", payload["decision"])

    case_by_id = {case["case_id"]: case for case in cases}
    price_case = case_by_id["RAG-018-SIM-C01"]
    assert_condition(price_case["retrieval_status"] == "influenced", price_case)
    assert_condition(price_case["retrieval_used_in_runtime"] is True, price_case)
    assert_condition(price_case["objection_resolution_delta"] == 1, price_case)
    assert_condition(price_case["next_step_quality_delta"] == 1, price_case)
    assert_condition("nicht am punkt vorbeirede" in price_case["rag_response"].lower(), price_case["rag_response"])

    send_info_case = case_by_id["RAG-018-SIM-C03"]
    assert_condition(send_info_case["retrieval_status"] == "influenced", send_info_case)
    assert_condition(send_info_case["retrieval_used_in_runtime"] is True, send_info_case)
    assert_condition(send_info_case["objection_resolution_delta"] == 1, send_info_case)
    assert_condition(send_info_case["next_step_quality_delta"] == 1, send_info_case)
    assert_condition("send" in send_info_case["rag_response"].lower(), send_info_case["rag_response"])
    assert_condition("information" in send_info_case["rag_response"].lower(), send_info_case["rag_response"])

    authority_case = case_by_id["RAG-018-SIM-C04"]
    assert_condition(authority_case["retrieval_status"] == "influenced", authority_case)
    assert_condition(authority_case["retrieval_used_in_runtime"] is True, authority_case)
    assert_condition(authority_case["objection_resolution_delta"] == 1, authority_case)
    assert_condition(authority_case["next_step_quality_delta"] == 1, authority_case)
    assert_condition("boss" in authority_case["rag_response"].lower(), authority_case["rag_response"])
    assert_condition("concern" in authority_case["rag_response"].lower(), authority_case["rag_response"])

    trust_case = case_by_id["RAG-018-SIM-C05"]
    assert_condition(trust_case["retrieval_status"] == "blocked", trust_case)
    assert_condition(trust_case["retrieval_used_in_runtime"] is False, trust_case)
    assert_condition("no payment" in trust_case["rag_response"].lower(), trust_case["rag_response"])
    assert_condition("verification path" in trust_case["rag_response"].lower(), trust_case["rag_response"])

    for case_id in ("RAG-018-SIM-C07", "RAG-018-SIM-C08", "RAG-018-SIM-C09", "RAG-018-SIM-C10"):
        protected = case_by_id[case_id]
        assert_condition(protected["protected_context"] is True, protected)
        assert_condition(protected["retrieval_used_in_runtime"] is False, protected)
        assert_condition(protected["protected_text_preserved"] is True, protected)

    for case in cases:
        assert_condition(case["safe"] is True, case)
        assert_condition(case["language_match"] is True, case)
        assert_condition(case["campaign_facts_override_rag"] is True, case)
        assert_condition(case["retrieval_elapsed_ms"] <= case["retrieval_acceptable_ms"], case)

    forbidden = [
        "data/private",
        "data/private-restricted",
        '"source_excerpt_text":',
        "you are anxious",
        "you are angry",
        "i can tell you feel",
        "discount ends",
        "only today",
        "guaranteed savings",
    ]
    for phrase in forbidden:
        assert_condition(phrase not in combined, f"Forbidden text leaked: {phrase}")

    assert_condition("scored objection resolution" in report.lower(), report)
    assert_condition("do not make retrieval default" in report.lower(), report)
    print("RAG-018 scripted call simulation validation passed.")


if __name__ == "__main__":
    main()
