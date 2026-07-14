#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.exp_002_frozen_response_baseline import (
    build_frozen_baseline_result,
    frozen_baseline_self_check,
    normalized_prompt_packet_digest,
)

RUNNER = ROOT / "scripts" / "run_exp_002_frozen_response_baseline.py"
RESULT = ROOT / "research" / "experiments" / "generated" / "EXP-002-frozen-response-baseline" / "result.json"
REPORT = RESULT.with_name("report.md")
TRACKED_PACKET = ROOT / "research" / "experiments" / "generated" / "EXP-002" / "EXP-002-prompt-packet.md"
RENDERED_PACKET = ROOT / ".tmp" / "exp-002-frozen-response-baseline" / "EXP-002-prompt-packet.md"
EXPECTED_NORMALIZED_PROMPT_PACKET_SHA256 = "83DF6E5F7B3566754F7D09C78F5BBD3B013ABED328C01EF90BA68BCFF2C395FA"
EXPECTED_SUMMARY = {
    "case_count": 6,
    "response_count": 12,
    "adaptive_preferred_count": 6,
    "non_adaptive_preferred_count": 0,
    "tie_count": 0,
    "non_adaptive_average_total": 18.67,
    "adaptive_average_total": 23.67,
}


def main() -> int:
    try:
        if not RUNNER.exists():
            raise AssertionError("missing frozen-response baseline runner")
        completed = subprocess.run(
            [sys.executable, str(RUNNER)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=60,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(completed.stdout + completed.stderr)
        recorded = json.loads(RESULT.read_text(encoding="utf-8"))
        expected = build_frozen_baseline_result(ROOT)
        if recorded != expected:
            raise AssertionError("recorded frozen-response baseline differs from deterministic rebuild")
        if recorded["summary"] != EXPECTED_SUMMARY:
            raise AssertionError("frozen-response baseline summary drift")
        if recorded["response_generation_performed"] is not False:
            raise AssertionError("baseline must not claim response regeneration")
        if recorded["semantic_judgment_recomputed"] is not False:
            raise AssertionError("baseline must not claim semantic re-evaluation")
        if recorded["evaluator_provenance_status"] != "not_recorded":
            raise AssertionError("baseline evaluator provenance must remain explicitly unrecorded")
        if recorded["score_arithmetic_recomputed"] is not True:
            raise AssertionError("baseline score arithmetic was not recomputed")
        report = REPORT.read_text(encoding="utf-8")
        for marker in (
            "Frozen EXP-002 Response Baseline",
            "Score arithmetic recomputed: `True`",
            "Response generation performed: `False`",
            "Semantic judgment recomputed: `False`",
            "Evaluator provenance status: `not_recorded`",
        ):
            if marker not in report:
                raise AssertionError(f"baseline report missing marker: {marker}")
        rendered = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "run_prompt_baseline.py"),
                "--cases",
                str(ROOT / "research" / "experiments" / "cases" / "exp-002-dataset-derived.json"),
                "--out",
                str(RENDERED_PACKET),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=60,
            check=False,
        )
        if rendered.returncode != 0:
            raise AssertionError(rendered.stdout + rendered.stderr)
        if normalized_prompt_packet_digest(TRACKED_PACKET) != EXPECTED_NORMALIZED_PROMPT_PACKET_SHA256:
            raise AssertionError("tracked normalized prompt packet drift")
        if normalized_prompt_packet_digest(RENDERED_PACKET) != EXPECTED_NORMALIZED_PROMPT_PACKET_SHA256:
            raise AssertionError("rerendered normalized prompt packet drift")
        if frozen_baseline_self_check(ROOT) != "pass":
            raise AssertionError("frozen baseline self-check failed")
    except (AssertionError, KeyError, OSError, ValueError) as exc:
        print(f"EXP-002 frozen-response baseline validation failed: {exc}")
        return 1
    print("EXP-002 frozen-response baseline validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
