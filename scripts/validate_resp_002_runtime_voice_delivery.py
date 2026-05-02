#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "generate_runtime_voice_delivery.py"
RESP_001_RUNNER = ROOT / "scripts" / "generate_guarded_response.py"
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "prod-005-realtime-latency-call-control.json"
TMP_DIR = ROOT / ".tmp" / "resp-002-validation"
RESULT_PATH = TMP_DIR / "RESP-002-runtime-voice-delivery-result.json"
REPORT_PATH = TMP_DIR / "RESP-002-runtime-voice-delivery-report.md"

SECRET_PATTERN = re.compile(
    r"(sk_car_[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|Authorization:\s*Bearer\s+[A-Za-z0-9]|X-API-Key\s*[:=]\s*[A-Za-z0-9]|xi-api-key\s*[:=]\s*[A-Za-z0-9])"
)


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True)


def parse_stdout_json(completed: subprocess.CompletedProcess[str]) -> dict:
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Expected JSON stdout, got: {completed.stdout!r}") from exc


def run_resp_002(transcript: str, stage: str = "relevance-check", provider: str = "elevenlabs") -> dict:
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--campaign",
            "campaign-prod-005-b2c-telecom",
            "--stage",
            stage,
            "--transcript",
            transcript,
            "--cases",
            str(CASES_PATH),
            "--provider",
            provider,
            "--out",
            str(RESULT_PATH),
            "--report-out",
            str(REPORT_PATH),
        ]
    )
    assert_condition(completed.returncode == 0, completed.stderr)
    return parse_stdout_json(completed)


def run_resp_001(transcript: str, stage: str = "relevance-check") -> dict:
    completed = run_command(
        [
            sys.executable,
            str(RESP_001_RUNNER),
            "--campaign",
            "campaign-prod-005-b2c-telecom",
            "--stage",
            stage,
            "--transcript",
            transcript,
            "--cases",
            str(CASES_PATH),
        ]
    )
    assert_condition(completed.returncode == 0, completed.stderr)
    return parse_stdout_json(completed)


def validate_common_payload(payload: dict, resp_001_payload: dict) -> None:
    voice_delivery = payload["voice_delivery"]
    assert_condition(payload["runtime_voice_delivery_id"] == "RESP-002-runtime-voice-delivery", payload)
    assert_condition(payload["response_generation_id"] == "RESP-001-local-guarded", payload)
    assert_condition(payload["final_response"] == resp_001_payload["final_response"], "RESP-002 must not change final_response.")
    assert_condition(voice_delivery["final_response_unchanged"] is True, voice_delivery)
    assert_condition(voice_delivery["provider_calls_made"] is False, voice_delivery)
    assert_condition(voice_delivery["requires_api_key"] is False, voice_delivery)
    assert_condition(voice_delivery["customer_audio_uploaded"] is False, voice_delivery)
    assert_condition(voice_delivery["voice_cloning_used"] is False, voice_delivery)
    assert_condition(voice_delivery["validation"]["passed"] is True, voice_delivery["validation"])
    assert_condition(
        voice_delivery["provider_rendering"]["protected_segment_provider_tag_count"] == 0,
        voice_delivery["provider_rendering"],
    )


def validate_freeform_payload(payload: dict) -> None:
    delivery = payload["voice_delivery"]
    assert_condition(delivery["segments"][0]["segment_type"] == "freeform_objection_handling", delivery["segments"])
    assert_condition(delivery["segments"][0]["eligible_for_prosody"] is True, delivery["segments"])
    assert_condition(delivery["prosody"]["cue_count"] > 0, delivery["prosody"])
    assert_condition(delivery["provider_rendering"]["provider_key"] == "elevenlabs", delivery["provider_rendering"])
    assert_condition(
        delivery["provider_rendering"]["rendered_text"] != payload["final_response"],
        "Eligible freeform response should get provider delivery shaping.",
    )


def validate_protected_payload(payload: dict, expected_segment_type: str) -> None:
    delivery = payload["voice_delivery"]
    segment = delivery["segments"][0]
    assert_condition(segment["segment_type"] == expected_segment_type, segment)
    assert_condition(segment["eligible_for_prosody"] is False, segment)
    assert_condition(delivery["prosody"]["cue_count"] == 0, delivery["prosody"])
    assert_condition(delivery["provider_rendering"]["provider_tag_count"] == 0, delivery["provider_rendering"])
    assert_condition(delivery["provider_rendering"]["rendered_text"] == payload["final_response"], delivery["provider_rendering"])


def assert_no_secret_text(text: str, label: str) -> None:
    match = SECRET_PATTERN.search(text)
    if match is not None:
        raise AssertionError(f"Potential secret-like value found in {label}: {match.group(0)!r}")


def main() -> None:
    assert_condition(RUNNER.exists(), "RESP-002 runner script is missing.")
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    freeform_transcript = "Das klingt zu teuer und ich weiss nicht, ob sich der Aufwand lohnt."
    freeform_payload = run_resp_002(freeform_transcript)
    freeform_resp_001 = run_resp_001(freeform_transcript)
    validate_common_payload(freeform_payload, freeform_resp_001)
    validate_freeform_payload(freeform_payload)

    do_not_call_transcript = "Rufen Sie mich bitte nicht mehr an."
    do_not_call_payload = run_resp_002(do_not_call_transcript)
    validate_common_payload(do_not_call_payload, run_resp_001(do_not_call_transcript))
    validate_protected_payload(do_not_call_payload, "do_not_call")

    claim_boundary_transcript = "Koennen Sie garantieren, dass ich damit Geld spare?"
    claim_boundary_payload = run_resp_002(claim_boundary_transcript)
    validate_common_payload(claim_boundary_payload, run_resp_001(claim_boundary_transcript))
    validate_protected_payload(claim_boundary_payload, "claim_boundary")

    human_request_transcript = "Ich will mit einem Menschen sprechen."
    human_request_payload = run_resp_002(human_request_transcript)
    validate_common_payload(human_request_payload, run_resp_001(human_request_transcript))
    validate_protected_payload(human_request_payload, "human_handoff_exact_script")

    assert_condition(RESULT_PATH.exists(), "RESP-002 JSON result file was not created.")
    assert_condition(REPORT_PATH.exists(), "RESP-002 Markdown report was not created.")
    assert_no_secret_text(
        RESULT_PATH.read_text(encoding="utf-8")
        + REPORT_PATH.read_text(encoding="utf-8")
        + json.dumps(freeform_payload, ensure_ascii=False),
        "RESP-002 artifacts",
    )
    print("RESP-002 runtime voice delivery validation passed.")


if __name__ == "__main__":
    main()
