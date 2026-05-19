#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "LIVE-DEMO-006-memory-transcript-visibility"
RUNNER = ROOT / "scripts" / "run_live_demo_001_agent_voice_call.py"
ROADMAP_PATH = ROOT / "docs" / "thesis" / "ROADMAP.md"
CHECKPOINT_INDEX_PATH = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
COMMANDS_PATH = ROOT / "docs" / "product" / "COMMANDS.md"
DOC_PATH = ROOT / "docs" / "product" / "LIVE_DEMO_006_MEMORY_TRANSCRIPT_VISIBILITY.md"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID
HTML_OUT = TMP_DIR / "live-demo-001.html"
METADATA_OUT = TMP_DIR / "live-demo-001-metadata.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_live_demo_002_conversation_stability import (  # noqa: E402
    append_turn,
    build_demo_turn,
    normalize,
)


def assert_condition(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def run_demo_export() -> tuple[str, dict[str, Any]]:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--export-html",
            str(HTML_OUT),
            "--export-metadata",
            str(METADATA_OUT),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=240,
    )
    if completed.returncode != 0:
        raise AssertionError(f"Live demo export failed: stdout={completed.stdout!r} stderr={completed.stderr!r}")
    return HTML_OUT.read_text(encoding="utf-8"), json.loads(METADATA_OUT.read_text(encoding="utf-8"))


def validate_transcript_visibility(failures: list[str], evidence: dict[str, Any]) -> None:
    html, metadata = run_demo_export()
    playback = metadata.get("playback", {})
    required_html_fragments = [
        'id="conversationTranscript"',
        'id="downloadTranscriptJson"',
        'id="downloadTranscriptText"',
        "const conversationTranscript = [];",
        "function appendConversationTranscriptTurn(",
        "function renderConversationTranscript()",
        "function downloadTranscript(",
        "demo_conversation_memory",
        "demo_conversation_stability_guard",
    ]
    evidence["transcript_visibility"] = {
        "playback_metadata": playback,
        "required_fragments": {fragment: fragment in html for fragment in required_html_fragments},
    }
    assert_condition(
        failures,
        playback.get("transcript_panel_enabled") is True,
        f"Playback metadata must expose transcript panel support: {playback}",
    )
    assert_condition(
        failures,
        playback.get("transcript_download_enabled") is True,
        f"Playback metadata must expose transcript download support: {playback}",
    )
    for fragment in required_html_fragments:
        assert_condition(failures, fragment in html, f"Live demo HTML missing transcript fragment: {fragment}")


def validate_memory_repetition_controls(failures: list[str], evidence: dict[str, Any]) -> None:
    state: dict[str, Any] = {"turns": []}
    records: list[dict[str, Any]] = []
    scenario = [
        "__agent_open__",
        "okay",
        "what is the price",
        "tell me more",
        "tell me more",
        "tell me more",
        "tell me more",
        "tell me more",
        "tell me more",
        "tell me more",
    ]
    for transcript in scenario:
        packet = build_demo_turn(transcript, state, session_id="live-demo-006-memory")
        records.append(
            {
                "transcript": transcript,
                "response": packet["summary"]["final_response"],
                "memory": packet.get("demo_conversation_memory", {}),
                "guard": packet.get("demo_conversation_stability_guard", {}),
            }
        )
        append_turn(state, packet)

    responses = [record["response"] for record in records]
    duplicates = sorted({response for response in responses if responses.count(response) > 1})
    last_memory = records[-1]["memory"]
    evidence["memory_repetition_controls"] = {
        "records": records,
        "duplicate_response_count": len(duplicates),
        "duplicates": duplicates,
        "last_memory": last_memory,
    }
    assert_condition(
        failures,
        not duplicates,
        f"Repeated same-focus follow-ups should not produce exact duplicate final responses: {duplicates}",
    )
    assert_condition(
        failures,
        isinstance(last_memory.get("last_response_signatures"), list) and last_memory.get("last_response_signatures"),
        f"Conversation memory should expose compact response signatures: {last_memory}",
    )
    assert_condition(
        failures,
        isinstance(last_memory.get("recent_response_subjects"), list) and last_memory.get("recent_response_subjects"),
        f"Conversation memory should expose recent response subjects: {last_memory}",
    )
    for response in responses:
        normalized = normalize(response)
        assert_condition(
            failures,
            all(internal not in normalized for internal in ["anti loop", "guardrail", "runtime", "decision log"]),
            f"Repetition repair must not leak internal wording: {response}",
        )


def validate_docs(failures: list[str], evidence: dict[str, Any]) -> None:
    doc_paths = [ROADMAP_PATH, CHECKPOINT_INDEX_PATH, COMMANDS_PATH, DOC_PATH]
    evidence["docs"] = {}
    for path in doc_paths:
        exists = path.exists()
        text = path.read_text(encoding="utf-8") if exists else ""
        evidence["docs"][str(path.relative_to(ROOT))] = {
            "exists": exists,
            "mentions_checkpoint": CHECKPOINT_ID in text,
        }
        assert_condition(failures, exists, f"Missing LIVE-DEMO-006 doc surface: {path.relative_to(ROOT)}")
        assert_condition(failures, CHECKPOINT_ID in text, f"{path.relative_to(ROOT)} does not mention {CHECKPOINT_ID}.")


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# LIVE-DEMO-006 Memory and Transcript Visibility Validator",
        "",
        f"- Passed: `{str(payload['passed']).lower()}`",
        f"- Failure count: `{payload['failure_count']}`",
        f"- Provider calls made: `{str(payload['provider_calls_made']).lower()}`",
        "",
        "## Failures",
        "",
    ]
    lines.extend([f"- {failure}" for failure in payload["failures"]] or ["- None"])
    if payload["passed"]:
        lines.extend(
            [
                "",
                "## Notes",
                "",
                "- The browser demo exposes a full local text transcript for the current session.",
                "- The transcript includes per-turn response, call control, memory, stability guard, and provider-boundary summary.",
                "- Conversation memory now includes compact response signatures and subjects for repetition diagnosis.",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    failures: list[str] = []
    evidence: dict[str, Any] = {}
    validate_transcript_visibility(failures, evidence)
    validate_memory_repetition_controls(failures, evidence)
    validate_docs(failures, evidence)

    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "passed": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "provider_calls_made": False,
        "evidence": evidence,
    }
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    REPORT_PATH.write_text(render_report(payload), encoding="utf-8")
    if failures:
        raise AssertionError(f"{CHECKPOINT_ID} failed with {len(failures)} issue(s). See {RESULT_PATH}.")
    print(f"{CHECKPOINT_ID} validation passed.")


if __name__ == "__main__":
    main()
