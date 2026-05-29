#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PACKET_RESULT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-LISTENING-REVIEW-001" / "result.json"
PACKET_REPORT = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-LISTENING-REVIEW-001" / "report.md"
MANUAL_TEMPLATE_JSON = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-LISTENING-REVIEW-MANUAL-001" / "manual_review_template.json"
MANUAL_TEMPLATE_MD = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-LISTENING-REVIEW-MANUAL-001" / "manual_review_template.md"
GENERATOR = ROOT / "scripts" / "generate_ultravox_audio_listening_review_packet_001.py"
SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|[A-Za-z0-9]{8}\.[A-Za-z0-9]{32}|ULTRAVOX_API_KEY\s*=\s*(?!\.\.\.|<redacted>|your-api-key)[^\s]+|PROJECT_ULTRAVOX_TOOL_TOKEN\s*=\s*(?!\.\.\.|<redacted>|your-token)[^\s]+|Authorization:\s*Bearer\s+[A-Za-z0-9]|X-API-Key:\s*(?!<redacted>|your-api-key)[A-Za-z0-9]|X-Project-Tool-Token:\s*(?!<redacted>|your-token)[A-Za-z0-9]|wss://[^\"'\s]+|https://voice\.ultravox\.ai/[^\"'\s]+)"
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


def assert_no_secret(label: str, text: str) -> None:
    match = SECRET_PATTERN.search(text)
    if match:
        fail(f"secret-like value found in {label}: {match.group(0)!r}")


def git_tracked(relative_path: str) -> bool:
    completed = subprocess.run(
        ["git", "ls-files", "--error-unmatch", relative_path],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.returncode == 0


def assert_false(payload: dict[str, Any], key: str) -> None:
    if payload.get(key) is not False:
        fail(f"{key} must be false")


def assert_common_boundaries(payload: dict[str, Any]) -> None:
    for key in (
        "new_provider_call_made",
        "new_audio_generated",
        "audio_files_copied",
        "audio_files_committed",
        "outbound_phone_call_made",
        "real_customer_data_used",
        "raw_private_audio_or_transcripts_used",
        "live_wiring_allowed",
        "production_call_allowed",
        "real_customer_data_allowed",
        "runtime_behavior_changed",
        "response_text_changed",
    ):
        assert_false(payload, key)


def main() -> None:
    packet = load_json(PACKET_RESULT)
    manual = load_json(MANUAL_TEMPLATE_JSON)
    report = PACKET_REPORT.read_text(encoding="utf-8") if PACKET_REPORT.is_file() else ""
    manual_md = MANUAL_TEMPLATE_MD.read_text(encoding="utf-8") if MANUAL_TEMPLATE_MD.is_file() else ""
    if not report:
        fail(f"missing file: {rel(PACKET_REPORT)}")
    if not manual_md:
        fail(f"missing file: {rel(MANUAL_TEMPLATE_MD)}")
    if not GENERATOR.is_file():
        fail(f"missing file: {rel(GENERATOR)}")
    assert_no_secret("listening packet evidence", json.dumps(packet) + json.dumps(manual) + report + manual_md)

    if packet.get("evaluation_id") != "ULTRAVOX-AUDIO-LISTENING-REVIEW-001":
        fail("unexpected listening review evaluation_id")
    if packet.get("phase") != "4J6":
        fail("listening review packet must record phase 4J6")
    if packet.get("status") != "pending_manual_review":
        fail("listening review status must stay pending_manual_review")
    if manual.get("status") != "pending_manual_review":
        fail("manual template status must stay pending_manual_review")
    if packet.get("audio_files_copied") is not False:
        fail("listening packet must not copy audio into evidence")
    assert_common_boundaries(packet)

    entries = packet.get("agent_audio_review_entries")
    if not isinstance(entries, list):
        fail("agent_audio_review_entries must be a list")
    if packet.get("agent_audio_review_entries_count") != len(entries):
        fail("agent_audio_review_entries_count must match entries")
    if not entries:
        fail("expected at least one agent audio review entry")
    for entry in entries:
        if not isinstance(entry, dict):
            fail("agent audio review entries must be objects")
        for key in (
            "local_audio_path",
            "duration_seconds",
            "sample_rate",
            "file_size_bytes",
            "waveform_hash",
            "associated_user_prompt",
            "associated_transcript_snippet",
            "agent_transcript_snippet",
            "first_audio_latency_seconds",
            "audio_files_copied",
            "audio_files_committed",
        ):
            if key not in entry:
                fail(f"agent audio review entry missing {key}")
        local_audio_path = str(entry["local_audio_path"]).replace("\\", "/")
        if not local_audio_path.startswith("local_artifacts/audio_outputs/ultravox/agent_outputs/"):
            fail(f"agent audio path outside local_artifacts agent output boundary: {local_audio_path}")
        if entry.get("audio_files_copied") is not False or entry.get("audio_files_committed") is not False:
            fail("agent audio entry must record no copied or committed audio")
        if git_tracked(local_audio_path):
            fail(f"agent audio file is tracked by Git: {local_audio_path}")
        if not isinstance(entry.get("file_size_bytes"), int) or entry["file_size_bytes"] <= 0:
            fail("agent audio entry must include a positive file_size_bytes")
        if not re.fullmatch(r"[a-f0-9]{64}", str(entry.get("waveform_hash") or "")):
            fail("agent audio entry must include a sha256 waveform_hash")

    checklist = manual.get("manual_listening_checklist")
    if not isinstance(checklist, list):
        fail("manual_listening_checklist must be a list")
    required_checklist = {
        "intelligibility",
        "naturalness",
        "voice_quality",
        "sales_tone",
        "pacing",
        "artifact_severity",
        "interruption_turn_taking_quality",
        "thesis_demo_suitability",
        "product_fallback_suitability",
        "compared_to_elevenlabs",
        "notes",
    }
    if {str(item.get("field")) for item in checklist if isinstance(item, dict)} != required_checklist:
        fail("manual checklist fields do not match the required review fields")

    required_report_lines = [
        "Status: `pending_manual_review`",
        "Agent audio review entries:",
        "Audio files copied: `false`",
        "Audio files committed: `false`",
        "New provider call made: `false`",
        "New audio generated: `false`",
        "Live wiring allowed: `false`",
        "Production call allowed: `false`",
        "Runtime behavior changed: `false`",
        "Response text changed: `false`",
    ]
    for line in required_report_lines:
        if line not in report:
            fail(f"listening review report missing line: {line}")

    print("ULTRAVOX audio listening review packet validation passed.")


if __name__ == "__main__":
    main()
