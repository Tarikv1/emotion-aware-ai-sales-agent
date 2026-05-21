#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_live_demo_001_agent_voice_call import (  # noqa: E402
    DEFAULT_CAMPAIGN_ID,
    DEFAULT_CASES_PATH,
    DEFAULT_STAGE,
    build_turn_packet,
)


CHECKPOINT_ID = "LIVE-DEMO-voice-id-diagnostics"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID
TEST_VOICE_ID = "test-voice-id-diagnostics-001"
TEST_VOICE_SHA = hashlib.sha256(TEST_VOICE_ID.encode("utf-8")).hexdigest()[:8]


def assert_condition(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# LIVE-DEMO Voice ID Diagnostics Validator",
        "",
        f"- Passed: `{str(payload['passed']).lower()}`",
        f"- Failure count: `{payload['failure_count']}`",
        "- Provider calls made: `false`",
        "",
        "## Failures",
        "",
    ]
    lines.extend([f"- {failure}" for failure in payload["failures"]] or ["- None"])
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Requires per-turn redacted voice-ID diagnostics.",
            "- Requires source, length, and short hash without logging the raw voice ID.",
            "- Runs in dry-run mode and must not call ElevenLabs.",
        ]
    )
    return "\n".join(lines)


def build_test_turn() -> dict[str, Any]:
    old_env = {
        "ELEVENLABS_VOICE_ID_EN": os.environ.get("ELEVENLABS_VOICE_ID_EN"),
        "ELEVENLABS_VOICE_ID": os.environ.get("ELEVENLABS_VOICE_ID"),
        "ELEVENLABS_VOICE_ID_DE": os.environ.get("ELEVENLABS_VOICE_ID_DE"),
    }
    try:
        os.environ["ELEVENLABS_VOICE_ID_EN"] = TEST_VOICE_ID
        os.environ.pop("ELEVENLABS_VOICE_ID", None)
        os.environ.pop("ELEVENLABS_VOICE_ID_DE", None)
        return build_turn_packet(
            transcript="__agent_open__",
            campaign_id=DEFAULT_CAMPAIGN_ID,
            stage=DEFAULT_STAGE,
            input_type="agent-open",
            silence_count=0,
            cases_path=DEFAULT_CASES_PATH,
            private_out=TMP_DIR,
            live_tts=False,
            force_key_missing=False,
            timeout_seconds=8.0,
            session_id="voice-id-diagnostics-test",
            session_state={"turns": []},
            asr_confidence=0.94,
            voice_turn_state="idle",
        )
    finally:
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def validate_voice_id_diagnostics(failures: list[str], evidence: dict[str, Any]) -> None:
    packet = build_test_turn()
    tts = packet.get("packet", {}).get("tts_delivery") or {}
    summary = packet.get("summary") or {}
    diagnostics = tts.get("voice_id_diagnostics") or {}

    evidence["diagnostics"] = diagnostics
    evidence["summary_voice_fields"] = {
        "tts_voice_id_source": summary.get("tts_voice_id_source"),
        "tts_voice_id_present": summary.get("tts_voice_id_present"),
        "tts_voice_id_length": summary.get("tts_voice_id_length"),
        "tts_voice_id_hash": summary.get("tts_voice_id_hash"),
    }
    evidence["provider_calls_made"] = summary.get("tts_provider_calls_made")

    assert_condition(failures, summary.get("tts_provider_calls_made") is False, "Validator must not call ElevenLabs.")
    assert_condition(failures, diagnostics.get("source") == "ELEVENLABS_VOICE_ID_EN", f"Voice source should identify the selected env var: {diagnostics}")
    assert_condition(failures, diagnostics.get("present") is True, f"Voice diagnostics should mark voice ID present: {diagnostics}")
    assert_condition(failures, diagnostics.get("length") == len(TEST_VOICE_ID), f"Voice diagnostics should include ID length: {diagnostics}")
    assert_condition(failures, diagnostics.get("sha256_8") == TEST_VOICE_SHA, f"Voice diagnostics should include short hash: {diagnostics}")
    assert_condition(failures, summary.get("tts_voice_id_source") == diagnostics.get("source"), f"Summary should mirror voice source: {summary}")
    assert_condition(failures, summary.get("tts_voice_id_hash") == TEST_VOICE_SHA, f"Summary should mirror voice hash: {summary}")

    serialized = json.dumps(packet, sort_keys=True)
    assert_condition(failures, TEST_VOICE_ID not in serialized, "Raw voice ID must not be written into packet or summary diagnostics.")


def main() -> None:
    failures: list[str] = []
    evidence: dict[str, Any] = {}
    validate_voice_id_diagnostics(failures, evidence)

    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "passed": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "provider_calls_made": False,
        "raw_voice_id_logged": False,
        "evidence": evidence,
    }
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    REPORT_PATH.write_text(render_report(payload), encoding="utf-8")
    if failures:
        raise AssertionError(f"{CHECKPOINT_ID} failed with {len(failures)} issue(s). See {RESULT_PATH}.")
    print(f"{CHECKPOINT_ID} validation passed.")


if __name__ == "__main__":
    main()
