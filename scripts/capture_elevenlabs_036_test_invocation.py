#!/usr/bin/env python3
"""Capture one ELEVENLABS-036 invocation with the shared sanitized transcript logic."""
from __future__ import annotations

import sys
from pathlib import Path

import capture_elevenlabs_039_test_invocation as capture


capture.CHECKPOINT_ID = "ELEVENLABS-036-natural-sales-scenarios"
tests_path = (
    Path(__file__).resolve().parents[1]
    / "runtime/providers/elevenlabs_agents/tests/web_design_natural_sales_scenarios_tests.json"
)
capture.EXPECTED_SYNTHETIC_EMAILS = {
    match.group(0).lower()
    for match in capture.EMAIL_RE.finditer(tests_path.read_text(encoding="utf-8"))
}


if __name__ == "__main__":
    sys.exit(capture.main())
