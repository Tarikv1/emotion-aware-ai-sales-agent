#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "LIVE-DEMO-005-interrupt-pace-plan-precision"
RUNNER = ROOT / "scripts" / "run_live_demo_001_agent_voice_call.py"
ROADMAP_PATH = ROOT / "docs" / "thesis" / "ROADMAP.md"
CHECKPOINT_INDEX_PATH = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
COMMANDS_PATH = ROOT / "docs" / "product" / "COMMANDS.md"
DOC_PATH = ROOT / "docs" / "product" / "LIVE_DEMO_005_INTERRUPT_PACE_PLAN_PRECISION.md"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID
HTML_OUT = TMP_DIR / "live-demo-001.html"
METADATA_OUT = TMP_DIR / "live-demo-001-metadata.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.voice.runtime_tts_delivery import LIVE_DEMO_STABLE_ELEVENLABS_VOICE_SETTINGS  # noqa: E402
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


def validate_manual_interrupt_and_pace(failures: list[str], evidence: dict[str, Any]) -> None:
    html, metadata = run_demo_export()
    playback = metadata.get("playback", {})
    stable_speed = float(LIVE_DEMO_STABLE_ELEVENLABS_VOICE_SETTINGS.get("speed") or 0)
    evidence["manual_interrupt_and_pace"] = {
        "playback_metadata": playback,
        "elevenlabs_stable_speed": stable_speed,
        "has_interrupt_button": 'id="interruptAgent"' in html,
        "has_interrupt_function": "function interruptAgentPlayback()" in html,
    }
    assert_condition(
        failures,
        playback.get("manual_interrupt_enabled") is True,
        f"Playback metadata must expose manual interrupt support: {playback}",
    )
    assert_condition(
        failures,
        playback.get("spoken_barge_in_enabled") is False,
        "Browser demo must not claim true spoken barge-in while browser ASR cannot safely ignore agent audio.",
    )
    assert_condition(
        failures,
        float(playback.get("browser_fallback_voice_rate") or 0) >= 1.0,
        f"Browser fallback voice should be about 5 percent faster than the prior 0.96 rate: {playback}",
    )
    assert_condition(
        failures,
        stable_speed >= 1.11,
        f"ElevenLabs live-demo stable speed should be about 5 percent faster than 1.06: {stable_speed}",
    )
    required_html_fragments = [
        'id="interruptAgent"',
        "function interruptAgentPlayback()",
        "audio.pause();",
        "window.speechSynthesis.cancel();",
        "setVoiceTurnState(VOICE_TURN_STATES.LISTENING",
        "utterance.rate = BROWSER_FALLBACK_VOICE_RATE;",
    ]
    for fragment in required_html_fragments:
        assert_condition(failures, fragment in html, f"Live demo HTML missing manual interrupt/pace fragment: {fragment}")


def plan_boundary_is_direct(response: str) -> bool:
    normalized = normalize(response)
    direct_negative = any(fragment in normalized for fragment in ["no", "not include", "does not include", "doesnt include"])
    mentions_plan_boundary = "starter" in normalized and "growth" in normalized
    mentions_features = "reminder" in normalized and "handoff" in normalized
    generic_restatement = normalized.startswith("starter covers basic lead capture and routing growth adds")
    return direct_negative and mentions_plan_boundary and mentions_features and not generic_restatement


def validate_product_plan_precision(failures: list[str], evidence: dict[str, Any]) -> None:
    state: dict[str, Any] = {"turns": []}
    records: list[dict[str, Any]] = []
    for transcript in [
        "__agent_open__",
        "okay",
        "what is the price",
        "so starter doesn't cover reminders and handoff review?",
        "so starter doesn't cover reminders and handoff review?",
    ]:
        packet = build_demo_turn(transcript, state, session_id="live-demo-005-plan-boundary")
        response = packet["summary"]["final_response"]
        records.append(
            {
                "transcript": transcript,
                "response": response,
                "continuity": packet.get("demo_session_continuity", {}),
                "memory": packet.get("demo_conversation_memory", {}),
                "guard": packet.get("demo_conversation_stability_guard", {}),
            }
        )
        append_turn(state, packet)

    price_response = records[2]["response"]
    first_boundary_response = records[3]["response"]
    second_boundary_response = records[4]["response"]
    first_memory = records[3]["memory"]
    evidence["product_plan_precision"] = records
    assert_condition(
        failures,
        "$29/month" in price_response and "$59/month" in price_response,
        f"Explicit price question should get the compact price answer even after qualification focus: {price_response}",
    )
    assert_condition(
        failures,
        plan_boundary_is_direct(first_boundary_response),
        f"Starter/Growth boundary answer should directly confirm the exclusion before steering: {first_boundary_response}",
    )
    assert_condition(
        failures,
        first_boundary_response != second_boundary_response,
        "Repeated plan-boundary question should not produce an exact duplicate final response.",
    )
    assert_condition(
        failures,
        "plan_boundary" in set(first_memory.get("answered_topics") or []),
        f"Conversation memory should record answered plan-boundary topics: {first_memory}",
    )
    assert_condition(
        failures,
        "anti-loop" not in normalize(first_boundary_response)
        and "guardrail" not in normalize(first_boundary_response)
        and "runtime" not in normalize(first_boundary_response),
        f"Plan-boundary repair must not leak internal wording: {first_boundary_response}",
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
        assert_condition(failures, exists, f"Missing LIVE-DEMO-005 doc surface: {path.relative_to(ROOT)}")
        assert_condition(failures, CHECKPOINT_ID in text, f"{path.relative_to(ROOT)} does not mention {CHECKPOINT_ID}.")


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# LIVE-DEMO-005 Interrupt, Pace, and Plan Precision Validator",
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
                "- Manual interrupt stops current browser/ElevenLabs playback and restarts listening only after local consent.",
                "- True spoken barge-in remains out of scope for this browser ASR demo.",
                "- Product plan-boundary questions answer directly before steering to the next sales step.",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    failures: list[str] = []
    evidence: dict[str, Any] = {}
    validate_manual_interrupt_and_pace(failures, evidence)
    validate_product_plan_precision(failures, evidence)
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
