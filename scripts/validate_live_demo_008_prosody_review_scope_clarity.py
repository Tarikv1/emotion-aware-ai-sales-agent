#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_live_demo_001_agent_voice_call import (  # noqa: E402
    DEFAULT_CASES_PATH,
    DEFAULT_CAMPAIGN_ID,
    DEFAULT_STAGE,
    build_turn_packet,
)
from scripts.validate_live_demo_002_conversation_stability import append_turn, normalize  # noqa: E402


CHECKPOINT_ID = "LIVE-DEMO-008-prosody-review-scope-clarity"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID

PRIVATE_TRANSCRIPT_FOLDER = ROOT / "data" / "private" / "live-demo-003" / "raw-turns" / "browser-transcript"


def assert_condition(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def build_live_turn(transcript: str, state: dict[str, Any], *, session_id: str, input_type: str = "speech-final") -> dict[str, Any]:
    return build_turn_packet(
        transcript=transcript,
        campaign_id=DEFAULT_CAMPAIGN_ID,
        stage=DEFAULT_STAGE,
        input_type=input_type,
        silence_count=0,
        cases_path=DEFAULT_CASES_PATH,
        private_out=TMP_DIR,
        live_tts=False,
        force_key_missing=False,
        timeout_seconds=8.0,
        session_id=session_id,
        session_state=state,
        asr_confidence=0.94,
        voice_turn_state="listening",
    )


def run_feedback_sequence() -> list[dict[str, Any]]:
    state: dict[str, Any] = {"turns": []}
    packets: list[dict[str, Any]] = []
    sequence = [
        ("__agent_open__", "agent-open"),
        ("yeah I guess sure", "speech-final"),
        (
            "I think assigning their reply is probably the biggest issue like not assigning completely but assigning it to the right person so there is no mixups",
            "speech-final",
        ),
        ("manual tracking I would say", "speech-final"),
        ("I don't really know", "speech-final"),
        (
            "I mean they do but like I said before I don't really know where exactly it's breaking I don't know if it's the callback or the lead or reminder or handoff status",
            "speech-final",
        ),
        ("I guess the callback reminders or workflow review", "speech-final"),
        ("yeah I guess", "speech-final"),
        ("I don't know would it", "speech-final"),
    ]
    for transcript, input_type in sequence:
        packet = build_live_turn(transcript, state, session_id="live-demo-008-feedback-repro", input_type=input_type)
        packets.append(packet)
        append_turn(state, packet)
    return packets


def has_bad_break(text: str) -> bool:
    bad_patterns = [
        r"\bcallback\s*<break\b[^>]*>\s*reminders\b",
        r"\bcall back\s*<break\b[^>]*>\s*reminders\b",
        r"\bcallback reminders\s*<break\b[^>]*>\s*are\b",
        r"\bowner\s*<break\b[^>]*>\s*and\s+reminder\b",
    ]
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in bad_patterns)


def validate_review_scope_clarity(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_feedback_sequence()
    focus_packets = packets[-2:]
    evidence["feedback_sequence"] = [
        {
            "turn": packet["session_turn_index"],
            "transcript": packet["transcript"],
            "response": packet["summary"]["final_response"],
            "tts_input_text": packet["summary"]["tts_input_text"],
            "provider_calls_made": packet["summary"]["tts_provider_calls_made"],
        }
        for packet in focus_packets
    ]
    forbidden_scope_phrases = {
        "would a short workflow review focus only on that gap",
        "should i keep the review",
        "which gap should the next step test first",
        "worth verified review",
    }
    for packet in focus_packets:
        response = packet["summary"]["final_response"]
        lowered = normalize(response)
        assert_condition(
            failures,
            not any(phrase in lowered for phrase in forbidden_scope_phrases),
            f"Response asks the buyer to decide internal review scope: {response}",
        )
        assert_condition(
            failures,
            any(fragment in lowered for fragment in {"i would keep", "the review would", "the next step would", "we would check", "they would check", "someone from northstar would check"}),
            f"Response should state what the agent/review would do before asking the buyer: {response}",
        )
        assert_condition(
            failures,
            any(fragment in lowered for fragment in {"right gap", "useful", "worth checking", "worth a check", "match what", "what time works", "quick call"}),
            f"Response should ask a buyer-relevant confirmation, not an internal scope question: {response}",
        )
        assert_condition(
            failures,
            packet["summary"]["tts_provider_calls_made"] is False,
            "Validator must not make live provider calls.",
        )


def validate_prosody_phrase_flow(failures: list[str], evidence: dict[str, Any]) -> None:
    packets = run_feedback_sequence()
    records = []
    for packet in packets:
        response = packet["summary"]["final_response"]
        tts_input = packet["summary"]["tts_input_text"]
        if "callback" not in response.lower() and "owner and reminder" not in response.lower():
            continue
        bad_break = has_bad_break(tts_input)
        records.append(
            {
                "turn": packet["session_turn_index"],
                "response": response,
                "tts_input_text": tts_input,
                "bad_break": bad_break,
            }
        )
        assert_condition(
            failures,
            not bad_break,
            f"TTS input inserted a break inside a tight sales phrase: {tts_input}",
        )
    evidence["prosody_phrase_flow"] = records
    assert_condition(failures, bool(records), "Prosody validation did not inspect any callback/owner phrase turns.")


def validate_docs_pending(failures: list[str], evidence: dict[str, Any]) -> None:
    evidence["private_transcript_folder"] = {
        "path": str(PRIVATE_TRANSCRIPT_FOLDER.relative_to(ROOT)),
        "exists": PRIVATE_TRANSCRIPT_FOLDER.exists(),
        "committed_by_validator": False,
    }
    assert_condition(failures, PRIVATE_TRANSCRIPT_FOLDER.exists(), "Expected private browser transcript folder is missing.")


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# LIVE-DEMO-008 Prosody and Review Scope Validator",
        "",
        f"- Passed: `{str(payload['passed']).lower()}`",
        f"- Failure count: `{payload['failure_count']}`",
        "- Provider calls made: `false`",
        "",
        "## Failures",
        "",
    ]
    if payload["failures"]:
        lines.extend(f"- {failure}" for failure in payload["failures"])
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Reproduces Tarik's callback-reminder review-scope feedback as a synthetic local sequence.",
            "- Checks that provider-rendered TTS does not break inside `callback reminders` or `owner and reminder`.",
            "- Checks that the agent states the review scope instead of asking the buyer to define internal review mechanics.",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    failures: list[str] = []
    evidence: dict[str, Any] = {}
    validate_review_scope_clarity(failures, evidence)
    validate_prosody_phrase_flow(failures, evidence)
    validate_docs_pending(failures, evidence)

    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "passed": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "provider_calls_made": False,
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
