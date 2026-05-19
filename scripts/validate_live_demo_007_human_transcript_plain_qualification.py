#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "LIVE-DEMO-007-human-readable-transcript-and-plain-qualification"
RUNNER = ROOT / "scripts" / "run_live_demo_001_agent_voice_call.py"
ROADMAP_PATH = ROOT / "docs" / "thesis" / "ROADMAP.md"
CHECKPOINT_INDEX_PATH = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
COMMANDS_PATH = ROOT / "docs" / "product" / "COMMANDS.md"
DOC_PATH = ROOT / "docs" / "product" / "LIVE_DEMO_007_HUMAN_TRANSCRIPT_PLAIN_QUALIFICATION.md"
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


JARGON_TERMS = {
    "shared inbox leads",
    "owner routing",
    "manager visibility",
    "owner lookup",
    "handoff review",
    "messy handoffs",
    "unclear owners",
    "where does that break",
    "slack alerts and crm notes",
}


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


def validate_transcript_ui(failures: list[str], evidence: dict[str, Any]) -> None:
    html, metadata = run_demo_export()
    transcript_index = html.find('id="conversationTranscript"')
    packet_index = html.find('id="packet"')
    evidence["transcript_ui"] = {
        "playback_metadata": metadata.get("playback", {}),
        "transcript_index": transcript_index,
        "packet_index": packet_index,
        "has_diagnostics_panel": 'id="conversationDiagnostics"' in html,
        "human_text_renderer_mentions_memory": "`Memory:" in html or "Memory: ${{" in html,
    }
    assert_condition(failures, transcript_index >= 0, "Conversation transcript element is missing.")
    assert_condition(failures, packet_index >= 0, "Turn packet element is missing.")
    assert_condition(
        failures,
        transcript_index < packet_index,
        "Conversation transcript should appear before the turn packet section.",
    )
    assert_condition(
        failures,
        'id="conversationDiagnostics"' in html,
        "Diagnostics should be available separately from the human transcript.",
    )
    assert_condition(
        failures,
        "`Memory:" not in html and "Memory: ${{" not in html,
        "Human transcript renderer should not show raw memory by default.",
    )
    assert_condition(
        failures,
        "function renderConversationDiagnosticsText()" in html,
        "Transcript diagnostics renderer is missing.",
    )
    assert_condition(
        failures,
        "demo_conversation_memory" in html,
        "JSON/debug transcript should still retain conversation memory for debugging.",
    )


def has_jargon(response: str) -> bool:
    normalized = normalize(response)
    return any(term in normalized for term in JARGON_TERMS)


def validate_plain_qualification(failures: list[str], evidence: dict[str, Any]) -> None:
    state: dict[str, Any] = {"turns": []}
    records: list[dict[str, Any]] = []
    scenario = [
        "__agent_open__",
        "maybe",
        "what do you mean by shared inbox lead",
        "I don't really know",
    ]
    for transcript in scenario:
        packet = build_demo_turn(transcript, state, session_id="live-demo-007-qualification")
        records.append(
            {
                "transcript": transcript,
                "response": packet["summary"]["final_response"],
                "continuity": packet.get("demo_session_continuity", {}),
            }
        )
        append_turn(state, packet)

    maybe_response = records[1]["response"]
    shared_inbox_response = records[2]["response"]
    unknown_response = records[3]["response"]
    evidence["plain_qualification"] = records

    assert_condition(
        failures,
        not has_jargon(maybe_response),
        f"`maybe` after opening should not trigger unexplained workflow jargon: {maybe_response}",
    )
    assert_condition(
        failures,
        "responsible" in normalize(maybe_response) or "reply" in normalize(maybe_response),
        f"`maybe` response should explain the simple sales check before diagnosing: {maybe_response}",
    )
    assert_condition(
        failures,
        "shared inbox" in normalize(shared_inbox_response)
        and ("one place" in normalize(shared_inbox_response) or "same inbox" in normalize(shared_inbox_response)),
        f"Shared-inbox clarification should define the term plainly: {shared_inbox_response}",
    )
    assert_condition(
        failures,
        not has_jargon(shared_inbox_response),
        f"Shared-inbox clarification should not replace one jargon term with another: {shared_inbox_response}",
    )
    assert_condition(
        failures,
        not has_jargon(unknown_response),
        f"`I don't know` should not jump to another jargon-heavy workflow sentence: {unknown_response}",
    )
    assert_condition(
        failures,
        "when someone asks for a demo" in normalize(unknown_response)
        or "who makes sure" in normalize(unknown_response),
        f"`I don't know` should ask one concrete plain-language diagnostic question: {unknown_response}",
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
        assert_condition(failures, exists, f"Missing LIVE-DEMO-007 doc surface: {path.relative_to(ROOT)}")
        assert_condition(failures, CHECKPOINT_ID in text, f"{path.relative_to(ROOT)} does not mention {CHECKPOINT_ID}.")


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# LIVE-DEMO-007 Human Transcript and Plain Qualification Validator",
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
                "- The visible browser transcript is human-first and appears before the raw turn packet.",
                "- Diagnostic memory remains available for JSON/debug review without cluttering the visible transcript.",
                "- Early qualification explains the product category before asking workflow-gap questions.",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    failures: list[str] = []
    evidence: dict[str, Any] = {}
    validate_transcript_ui(failures, evidence)
    validate_plain_qualification(failures, evidence)
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
