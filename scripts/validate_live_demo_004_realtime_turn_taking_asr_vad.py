#!/usr/bin/env python3
from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "LIVE-DEMO-004-realtime-turn-taking-asr-vad"
RUNNER = ROOT / "scripts" / "run_live_demo_001_agent_voice_call.py"
POLICY_PATH = ROOT / "runtime" / "speech" / "realtime_turn_taking_policy.py"
MANIFEST_PATH = ROOT / "runtime" / "runtime_manifest.json"
ROADMAP_PATH = ROOT / "docs" / "thesis" / "ROADMAP.md"
CHECKPOINT_INDEX_PATH = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
COMMANDS_PATH = ROOT / "docs" / "product" / "COMMANDS.md"
DOC_PATH = ROOT / "docs" / "product" / "LIVE_DEMO_004_REALTIME_TURN_TAKING_ASR_VAD.md"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / "LIVE-DEMO-004"
HTML_OUT = TMP_DIR / "live-demo-001.html"
METADATA_OUT = TMP_DIR / "live-demo-001-metadata.json"


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
            "--elevenlabs-env-file",
            str(TMP_DIR / "missing-elevenlabs.env"),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise AssertionError(f"Live demo export failed: stdout={completed.stdout!r} stderr={completed.stderr!r}")
    return HTML_OUT.read_text(encoding="utf-8"), json.loads(METADATA_OUT.read_text(encoding="utf-8"))


def load_policy_module(failures: list[str]) -> Any | None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    try:
        return importlib.import_module("runtime.speech.realtime_turn_taking_policy")
    except Exception as exc:  # noqa: BLE001 - validator should record import errors.
        failures.append(f"Could not import runtime speech turn-taking policy: {exc}")
        return None


def validate_policy_module(failures: list[str], evidence: dict[str, Any]) -> None:
    assert_condition(failures, POLICY_PATH.exists(), f"Missing runtime policy file: {POLICY_PATH.relative_to(ROOT)}")
    module = load_policy_module(failures)
    if module is None:
        return
    policy = module.realtime_turn_taking_policy()
    evidence["policy"] = policy
    assert_condition(failures, policy["checkpoint_id"] == CHECKPOINT_ID, f"Policy checkpoint mismatch: {policy}")
    assert_condition(failures, policy["browser_asr_is_true_vad"] is False, "Browser SpeechRecognition must not be claimed as true VAD.")
    assert_condition(failures, policy["raw_audio_uploaded_to_python_server"] is False, "LIVE-DEMO-004 must not upload raw audio to Python.")
    assert_condition(failures, policy["requires_final_result_for_auto_submit"] is True, "Auto-submit must require a final ASR result.")
    assert_condition(failures, policy["submit_on_interim_results"] is False, "Interim ASR results must not auto-submit.")
    assert_condition(failures, policy["cancel_pending_submit_on_interim_change"] is True, "Interim changes must cancel pending submit.")
    assert_condition(failures, policy["final_transcript_submit_delay_ms"] >= 1800, "Pause delay should be long enough for thinking pauses.")
    assert_condition(failures, policy["min_listening_window_before_submit_ms"] >= 1200, "Listening window should prevent instant submit after restart.")

    cases = [
        (
            "interim_not_submitted",
            module.should_auto_submit_browser_asr(
                transcript="I mean the callback thing is",
                confidence=0.93,
                voice_turn_state="listening",
                turn_in_flight=False,
                has_final_result=False,
                listening_elapsed_ms=5000,
            ),
            False,
            "wait_for_final_result",
        ),
        (
            "final_waits_for_min_window",
            module.should_auto_submit_browser_asr(
                transcript="callbacks are the problem",
                confidence=0.93,
                voice_turn_state="listening",
                turn_in_flight=False,
                has_final_result=True,
                listening_elapsed_ms=500,
            ),
            False,
            "minimum_listening_window",
        ),
        (
            "final_after_pause_accepted",
            module.should_auto_submit_browser_asr(
                transcript="callbacks are the problem",
                confidence=0.93,
                voice_turn_state="listening",
                turn_in_flight=False,
                has_final_result=True,
                listening_elapsed_ms=5000,
            ),
            True,
            "accepted",
        ),
        (
            "agent_speaking_rejected",
            module.should_auto_submit_browser_asr(
                transcript="that is interesting",
                confidence=0.93,
                voice_turn_state="agent_speaking",
                turn_in_flight=False,
                has_final_result=True,
                listening_elapsed_ms=5000,
            ),
            False,
            "agent_not_listening",
        ),
        (
            "low_confidence_rejected",
            module.should_auto_submit_browser_asr(
                transcript="callback problem",
                confidence=0.2,
                voice_turn_state="listening",
                turn_in_flight=False,
                has_final_result=True,
                listening_elapsed_ms=5000,
            ),
            False,
            "low_confidence",
        ),
        (
            "fragment_rejected",
            module.should_auto_submit_browser_asr(
                transcript="I want to talk about the",
                confidence=0.93,
                voice_turn_state="listening",
                turn_in_flight=False,
                has_final_result=True,
                listening_elapsed_ms=5000,
            ),
            False,
            "fragment",
        ),
    ]
    evidence["policy_cases"] = {name: result for name, result, _expected, _reason in cases}
    for name, result, expected, reason in cases:
        assert_condition(failures, result.get("accepted") is expected, f"{name} accepted mismatch: {result}")
        assert_condition(failures, result.get("reason") == reason, f"{name} reason mismatch: {result}")


def validate_metadata_and_html(failures: list[str], evidence: dict[str, Any]) -> None:
    html, metadata = run_demo_export()
    browser_asr = metadata.get("browser_asr", {})
    policy = browser_asr.get("turn_taking_policy", {})
    acceptance_policy = browser_asr.get("acceptance_policy", {})
    turn_taking = metadata.get("turn_taking", {})
    evidence["metadata_policy"] = policy
    assert_condition(failures, policy.get("checkpoint_id") == CHECKPOINT_ID, f"Metadata missing LIVE-DEMO-004 policy: {policy}")
    assert_condition(failures, acceptance_policy.get("final_transcript_submit_delay_ms", 0) >= 1800, "Metadata ASR final-submit delay is too short.")
    assert_condition(failures, policy.get("requires_final_result_for_auto_submit") is True, "Metadata should require final ASR result.")
    assert_condition(failures, policy.get("submit_on_interim_results") is False, "Metadata should block interim auto-submit.")
    assert_condition(failures, policy.get("raw_audio_uploaded_to_python_server") is False, "Metadata should preserve no raw audio upload.")
    assert_condition(failures, turn_taking.get("listen_while_agent_speaks") is False, "Turn-taking must not listen while agent speaks.")
    assert_condition(failures, turn_taking.get("listen_while_turn_in_flight") is False, "Turn-taking must not listen while a turn is in flight.")
    assert_condition(failures, metadata.get("boundaries", {}).get("opens_prod_102") is False, "LIVE-DEMO-004 must not open PROD-102.")

    required_fragments = [
        "const TURN_TAKING_POLICY = metadata.browser_asr.turn_taking_policy;",
        "const REQUIRE_FINAL_RESULT_FOR_AUTO_SUBMIT = TURN_TAKING_POLICY.requires_final_result_for_auto_submit;",
        "const SUBMIT_ON_INTERIM_RESULTS = TURN_TAKING_POLICY.submit_on_interim_results;",
        "const MIN_LISTENING_WINDOW_BEFORE_SUBMIT_MS = TURN_TAKING_POLICY.min_listening_window_before_submit_ms;",
        "let lastResultHadFinal = false;",
        "let listeningStartedAt = 0;",
        "function clearFinalSubmitTimer()",
        "if (!sawFinalResult && REQUIRE_FINAL_RESULT_FOR_AUTO_SUBMIT)",
        "clearFinalSubmitTimer();",
        "return { accepted: false, reason: \"wait_for_final_result\" };",
    ]
    for fragment in required_fragments:
        assert_condition(failures, fragment in html, f"Live demo HTML missing turn-taking fragment: {fragment}")


def validate_docs_and_manifest(failures: list[str], evidence: dict[str, Any]) -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest_paths = {entry.get("path") for entry in manifest.get("runtime_entries", [])}
    expected_path = "runtime/speech/realtime_turn_taking_policy.py"
    assert_condition(failures, expected_path in manifest_paths, "Runtime manifest missing realtime turn-taking policy.")
    for path in [ROADMAP_PATH, CHECKPOINT_INDEX_PATH, COMMANDS_PATH, DOC_PATH]:
        assert_condition(failures, path.exists(), f"Missing LIVE-DEMO-004 doc or command surface: {path.relative_to(ROOT)}")
        if path.exists():
            text = path.read_text(encoding="utf-8")
            assert_condition(failures, CHECKPOINT_ID in text, f"{path.relative_to(ROOT)} does not mention {CHECKPOINT_ID}.")
            assert_condition(failures, "PROD-102" in text, f"{path.relative_to(ROOT)} should preserve PROD-102 boundary.")
    evidence["manifest_runtime_entry_count"] = len(manifest.get("runtime_entries", []))


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# LIVE-DEMO-004 Realtime Turn-Taking ASR/VAD Validator",
        "",
        f"- Passed: `{str(payload['passed']).lower()}`",
        f"- Failure count: `{payload['failure_count']}`",
        f"- Provider calls made: `{str(payload['provider_calls_made']).lower()}`",
        f"- Browser ASR claimed true VAD: `{str(payload['evidence'].get('policy', {}).get('browser_asr_is_true_vad')).lower()}`",
        "",
        "## Failures",
        "",
    ]
    lines.extend([f"- {failure}" for failure in payload["failures"]] or ["- None"])
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- This validator is offline and does not use live microphone, provider ASR, provider TTS, or provider LLM calls.",
            "- Browser SpeechRecognition remains a browser-vendor ASR source, not a production VAD stack.",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    failures: list[str] = []
    evidence: dict[str, Any] = {}
    validate_policy_module(failures, evidence)
    validate_metadata_and_html(failures, evidence)
    validate_docs_and_manifest(failures, evidence)
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
