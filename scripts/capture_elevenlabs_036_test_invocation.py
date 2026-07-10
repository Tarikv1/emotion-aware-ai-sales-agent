#!/usr/bin/env python3
"""Capture and sanitize one live ELEVENLABS-036 test invocation."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import capture_elevenlabs_039_test_invocation as capture


CHECKPOINT_ID = "ELEVENLABS-036-natural-sales-scenarios"
SYNTHETIC_EMAILS = {
    "hello@cedarridgeglass.com",
    "oakwoodkidsdental@gmail.com",
    "sunrisebagelprovidence@gmail.com",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture one live ELEVENLABS-036 test invocation read-only.")
    parser.add_argument("--invocation-id", required=True, help="ElevenLabs test invocation ID")
    parser.add_argument("--output", required=True, type=Path, help="Required sanitized JSON output path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    api_key = os.environ.get(capture.API_KEY_ENV_VAR)
    if not api_key:
        print(f"error: {capture.API_KEY_ENV_VAR} is required", file=sys.stderr)
        return 2
    invocation_id = str(args.invocation_id).strip()
    if not invocation_id:
        print("error: --invocation-id must not be empty", file=sys.stderr)
        return 2

    capture.CHECKPOINT_ID = CHECKPOINT_ID
    capture.EXPECTED_SYNTHETIC_EMAILS = SYNTHETIC_EMAILS
    try:
        response = capture.json_request(
            "GET",
            f"/v1/convai/test-invocations/{quote(invocation_id, safe='')}",
            api_key=api_key,
        )
        raw = response.get("response")
        if not isinstance(raw, dict):
            raise ValueError("provider response must be a JSON object")
        payload = capture.build_sanitized_payload(raw, invocation_id)
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        output = {
            "captured_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "payload_sha256": hashlib.sha256(canonical).hexdigest(),
            "payload": payload,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(output, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    except Exception as exc:
        print(f"error: {capture.redact_text(str(exc))}", file=sys.stderr)
        return 1

    print(json.dumps({"status": "captured", "invocation_id": invocation_id, "output": str(args.output)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
