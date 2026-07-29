#!/usr/bin/env python3
from __future__ import annotations

import sys

import capture_elevenlabs_039_test_invocation as capture


capture.CHECKPOINT_ID = "ELEVENLABS-040-detailed-pricing-control"
capture.EXPECTED_SYNTHETIC_EMAILS = set()
CHECKPOINT_ID = capture.CHECKPOINT_ID
EXPECTED_SYNTHETIC_EMAILS = capture.EXPECTED_SYNTHETIC_EMAILS


if __name__ == "__main__":
    raise SystemExit(capture.main())
