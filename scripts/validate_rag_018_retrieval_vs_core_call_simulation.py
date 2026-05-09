#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_rag_018_retrieval_vs_core_call_simulation.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "rag-018-retrieval-vs-core-call-simulation.json"
RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "RAG-018-retrieval-vs-core-call-simulation" / "result.json"
REPORT_PATH = ROOT / "research" / "experiments" / "generated" / "RAG-018-retrieval-vs-core-call-simulation" / "report.md"
DOC_PATH = ROOT / "docs" / "product" / "RAG_018_GUARDED_RUNTIME_RETRIEVAL.md"

EXPECTED_CALL_COUNT = 4
EXPECTED_TURN_COUNT = 12
EXPECTED_RETRIEVAL_WINS = 4


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=90)


def main() -> None:
    assert_condition(RUNNER.exists(), "RAG-018 retrieval-vs-core call simulation runner is missing.")
    assert_condition(CASE_PATH.exists(), "RAG-018 retrieval-vs-core call simulation case file is missing.")
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
    turns = payload["turns"]
    combined = (json.dumps(payload, ensure_ascii=False).lower() + "\n" + report.lower()).replace("\\", "/")

    assert_condition(payload["simulation_id"] == "RAG-018-retrieval-vs-core-call-simulation", payload)
    assert_condition(payload["provider_calls_made"] is False, payload)
    assert_condition(payload["private_customer_data_used"] is False, payload)
    assert_condition(payload["llm_used"] is False, payload)
    assert_condition(payload["external_vector_db_used"] is False, payload)
    assert_condition(payload["embedding_provider_used"] is False, payload)
    assert_condition(summary["call_count"] == EXPECTED_CALL_COUNT, summary)
    assert_condition(summary["turn_count"] == EXPECTED_TURN_COUNT, summary)
    assert_condition(summary["safe_turn_count"] == EXPECTED_TURN_COUNT, summary)
    assert_condition(summary["unsafe_turn_count"] == 0, summary)
    assert_condition(summary["retrieval_turn_wins"] == EXPECTED_RETRIEVAL_WINS, summary)
    assert_condition(summary["core_turn_wins"] == 0, summary)
    assert_condition(summary["retrieval_total_score"] > summary["core_total_score"], summary)
    assert_condition(summary["score_delta"] > 0, summary)
    assert_condition(summary["protected_turns_preserved"] == summary["protected_turn_count"], summary)
    assert_condition(summary["retrieval_over_acceptable_count"] == 0, summary)
    assert_condition(payload["decision"] == "keep_retrieval_opt_in_for_validated_objection_turns", payload["decision"])

    turn_by_id = {turn["turn_id"]: turn for turn in turns}
    for turn_id in (
        "RAG-018-CALL-01-T01",
        "RAG-018-CALL-01-T02",
        "RAG-018-CALL-01-T03",
        "RAG-018-CALL-02-T01",
    ):
        turn = turn_by_id[turn_id]
        assert_condition(turn["winner"] == "retrieval", turn)
        assert_condition(turn["retrieval_used_in_runtime"] is True, turn)
        assert_condition(turn["score_delta"] > 0, turn)

    for turn in turns:
        assert_condition(turn["safe"] is True, turn)
        assert_condition(turn["language_match"] is True, turn)
        assert_condition(turn["campaign_facts_override_rag"] is True, turn)
        assert_condition(turn["retrieval_elapsed_ms"] <= turn["retrieval_acceptable_ms"], turn)
        if turn["protected_context"]:
            assert_condition(turn["winner"] == "tie", turn)
            assert_condition(turn["protected_text_preserved"] is True, turn)
            assert_condition(turn["retrieval_used_in_runtime"] is False, turn)

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
        "guaranteed conversion",
    ]
    for token in forbidden:
        assert_condition(token not in combined, token)

    assert_condition("retrieval version wins" in report.lower(), report)
    assert_condition("core version wins: `0`" in report.lower(), report)
    assert_condition("do not make retrieval default" in report.lower(), report)

    doc = DOC_PATH.read_text(encoding="utf-8").lower()
    assert_condition("rag-018 retrieval-vs-core call simulation" in doc, DOC_PATH)
    assert_condition("validate_rag_018_retrieval_vs_core_call_simulation.py" in doc, DOC_PATH)

    print("RAG-018 retrieval-vs-core call simulation validation passed.")


if __name__ == "__main__":
    main()
