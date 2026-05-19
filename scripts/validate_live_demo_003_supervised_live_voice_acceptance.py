#!/usr/bin/env python3
from __future__ import annotations

import json
import csv
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE_SCRIPT = ROOT / "scripts" / "generate_live_demo_003_acceptance_packet.py"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / "LIVE-DEMO-003-supervised-live-voice-acceptance"
TMP_DIR = ROOT / ".tmp" / "LIVE-DEMO-003"
RESULT_OUT = GENERATED_DIR / "result.json"
REPORT_OUT = GENERATED_DIR / "report.md"
SAMPLE_REVIEW_FORM = TMP_DIR / "manual_review_form.md"
SAMPLE_REVIEW_CSV = TMP_DIR / "manual_review.csv"
CHECKPOINT_ID = "LIVE-DEMO-003-supervised-live-voice-acceptance"


def assert_condition(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_acceptance_tool(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ACCEPTANCE_SCRIPT), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


def validate_schema(
    packet: dict[str, Any],
    report_text: str,
    review_form_text: str,
    review_csv_text: str,
    failures: list[str],
) -> None:
    assert_condition(failures, packet.get("checkpoint_id") == CHECKPOINT_ID, f"Wrong checkpoint id: {packet.get('checkpoint_id')}")
    for field in [
        "demo_session_id",
        "campaign_id",
        "live_tts_enabled",
        "browser_fallback_voice_used",
        "asr_used",
        "provider_tts_used",
        "llm_enrichment_enabled",
        "provider_llm_call_occurred",
        "durable_provider_agent_created",
        "voice_cloning_used",
        "turns",
        "manual_review_schema",
        "hard_gates",
        "human_quality_gates",
        "acceptance_result",
        "recommended_spoken_test_path",
        "optional_stress_turns",
    ]:
        assert_condition(failures, field in packet, f"Acceptance packet missing {field}")
    assert_condition(failures, isinstance(packet.get("turns"), list) and packet["turns"], "Acceptance packet should include turns")
    required_turn_fields = {
        "turn_index",
        "transcript",
        "final_response",
        "call_control",
        "demo_conversation_memory",
        "demo_conversation_stability_guard",
        "async_enrichment_boundary_packet",
        "server_latency_ms",
        "tts_latency_ms",
        "audio_uploaded_to_python_server",
        "manual_review",
    }
    for turn in packet.get("turns", []):
        missing = required_turn_fields.difference(turn)
        assert_condition(failures, not missing, f"Turn missing fields {sorted(missing)}: {turn}")
    manual_fields = set(packet.get("manual_review_schema", {}).get("fields", []))
    field_help = packet.get("manual_review_schema", {}).get("field_help", {})
    for field in [
        "asr_captured_correctly",
        "agent_interrupted_or_talked_over_user",
        "turn_taking_felt_natural",
        "response_latency_felt_acceptable",
        "voice_consistency",
        "response_naturalness",
        "sales_steering",
        "repeated_itself",
        "echoed_customer_too_much",
        "callback_confusion_seen",
        "buyer_agency_preserved",
        "notes",
        "accepted_for_next_iteration",
    ]:
        assert_condition(failures, field in manual_fields, f"Manual review schema missing {field}")
        assert_condition(failures, field in field_help, f"Manual review field help missing {field}")
    hard_gate_names = set(packet.get("hard_gates", {}).keys())
    for field in [
        "no_provider_hosted_durable_agent",
        "no_voice_cloning",
        "no_customer_audio_upload_to_python_server",
        "no_llm_blocking_live_spoken_response",
        "no_llm_mutation_of_final_response",
        "no_payment_collection",
        "no_bare_workflow_callback_treated_as_scheduling",
        "explicit_call_me_back_later_still_schedules",
        "terminal_call_control_stops_listening_restart",
        "no_exact_repeated_final_response",
        "no_obvious_customer_sentence_echoing",
        "no_internal_wording_leaked",
    ]:
        assert_condition(failures, field in hard_gate_names, f"Hard gate missing {field}")
    human_gate_names = set(packet.get("human_quality_gates", {}).keys())
    for field in [
        "turn_taking_average_min",
        "latency_acceptability_average_min",
        "voice_consistency_average_min",
        "response_naturalness_average_min",
        "sales_steering_average_min",
        "buyer_agency_preserved_required",
        "accepted_for_next_iteration_required",
    ]:
        assert_condition(failures, field in human_gate_names, f"Human quality gate missing {field}")
    assert_condition(failures, "# LIVE-DEMO-003" in report_text, "Acceptance report missing heading")
    assert_condition(failures, "sample scenarios only" in report_text.lower(), "Report should say scripted paths are samples only")
    assert_condition(failures, "JSON packet is the machine artifact" in review_form_text, "Review form should explain that JSON is machine-facing")
    assert_condition(failures, "## Field Guide" in review_form_text and "## Turn Review" in review_form_text, "Review form missing field guide or turn review")
    assert_condition(failures, "turn_index,transcript,final_response" in review_csv_text, "Review CSV missing expected leading columns")
    for field in manual_fields:
        assert_condition(failures, field in review_csv_text.splitlines()[0], f"Review CSV header missing {field}")


def validate_boundaries(packet: dict[str, Any], failures: list[str]) -> None:
    assert_condition(failures, packet.get("live_tts_enabled") is False, "Live TTS should be disabled by default")
    assert_condition(failures, packet.get("provider_tts_used") is False, "Provider TTS should not be used by default")
    assert_condition(failures, packet.get("provider_llm_call_occurred") is False, "LLM provider calls should not occur by default")
    assert_condition(failures, packet.get("durable_provider_agent_created") is False, "Durable provider agent must not be created")
    assert_condition(failures, packet.get("voice_cloning_used") is False, "Voice cloning must remain false")
    assert_condition(
        failures,
        all(turn.get("audio_uploaded_to_python_server") is False for turn in packet.get("turns", [])),
        "Customer audio must not be uploaded to the Python server",
    )
    assert_condition(
        failures,
        all((turn.get("async_enrichment_boundary_packet") or {}).get("provider_call_made") is False for turn in packet.get("turns", [])),
        "Async enrichment provider call should be false in default acceptance packet",
    )
    runner_source = (ROOT / "scripts" / "run_live_demo_001_agent_voice_call.py").read_text(encoding="utf-8")
    forbidden_turn_caps = [
        'session_state["turns"] = session_state["turns"][-8:]',
        'session_state["turns"] = session_state["turns"][-12:]',
        'session_state["turns"] = session_state["turns"][-20:]',
        'session_state["turns"] = session_state["turns"][-30:]',
    ]
    assert_condition(
        failures,
        not any(fragment in runner_source for fragment in forbidden_turn_caps),
        "Live demo runner should not reintroduce a fixed hard turn cap",
    )


def fill_review(packet: dict[str, Any], *, passing: bool) -> dict[str, Any]:
    clone = json.loads(json.dumps(packet))
    for turn in clone["turns"]:
        turn["manual_review"] = {
            "asr_captured_correctly": True if passing else False,
            "agent_interrupted_or_talked_over_user": False if passing else True,
            "turn_taking_felt_natural": 4 if passing else 2,
            "response_latency_felt_acceptable": 4 if passing else 2,
            "voice_consistency": 4 if passing else 2,
            "response_naturalness": 3 if passing else 2,
            "sales_steering": 4 if passing else 2,
            "repeated_itself": False if passing else True,
            "echoed_customer_too_much": False if passing else True,
            "callback_confusion_seen": False if passing else True,
            "buyer_agency_preserved": True if passing else False,
            "notes": "validator sample",
            "accepted_for_next_iteration": True if passing else False,
        }
    return clone


def write_review_csv(packet: dict[str, Any], path: Path, *, passing: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["turn_index", "transcript", "final_response", *packet["manual_review_schema"]["fields"]]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for turn in packet["turns"]:
            writer.writerow(
                {
                    "turn_index": turn["turn_index"],
                    "transcript": turn["transcript"],
                    "final_response": turn["final_response"],
                    "asr_captured_correctly": "true" if passing else "false",
                    "agent_interrupted_or_talked_over_user": "false" if passing else "true",
                    "turn_taking_felt_natural": "4" if passing else "2",
                    "response_latency_felt_acceptable": "4" if passing else "2",
                    "voice_consistency": "4" if passing else "2",
                    "response_naturalness": "3" if passing else "2",
                    "sales_steering": "4" if passing else "2",
                    "repeated_itself": "false" if passing else "true",
                    "echoed_customer_too_much": "false" if passing else "true",
                    "callback_confusion_seen": "false" if passing else "true",
                    "buyer_agency_preserved": "true" if passing else "false",
                    "notes": "validator csv sample",
                    "accepted_for_next_iteration": "true" if passing else "false",
                }
            )


def validate_review_outcomes(packet: dict[str, Any], failures: list[str]) -> dict[str, Any]:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    import scripts.generate_live_demo_003_acceptance_packet as acceptance  # noqa: E402

    passing_result = acceptance.evaluate_acceptance(fill_review(packet, passing=True))
    failing_result = acceptance.evaluate_acceptance(fill_review(packet, passing=False))
    assert_condition(
        failures,
        passing_result["status"] == "accepted_for_next_iteration",
        f"Passing sample review should be accepted: {passing_result}",
    )
    assert_condition(
        failures,
        failing_result["status"] == "not_accepted",
        f"Failing sample review should be not accepted: {failing_result}",
    )
    passing_csv = TMP_DIR / "passing_manual_review.csv"
    failing_csv = TMP_DIR / "failing_manual_review.csv"
    passing_packet = TMP_DIR / "passing_acceptance_packet.json"
    failing_packet = TMP_DIR / "failing_acceptance_packet.json"
    write_review_csv(packet, passing_csv, passing=True)
    write_review_csv(packet, failing_csv, passing=False)
    passing_completed = run_acceptance_tool(
        "--input",
        str(TMP_DIR / "acceptance_packet.json"),
        "--manual-review-csv",
        str(passing_csv),
        "--out",
        str(passing_packet),
        "--report-out",
        str(TMP_DIR / "passing_acceptance_report.md"),
        "--review-form-out",
        str(TMP_DIR / "passing_review_form.md"),
        "--review-csv-out",
        str(TMP_DIR / "passing_review_roundtrip.csv"),
    )
    failing_completed = run_acceptance_tool(
        "--input",
        str(TMP_DIR / "acceptance_packet.json"),
        "--manual-review-csv",
        str(failing_csv),
        "--out",
        str(failing_packet),
        "--report-out",
        str(TMP_DIR / "failing_acceptance_report.md"),
        "--review-form-out",
        str(TMP_DIR / "failing_review_form.md"),
        "--review-csv-out",
        str(TMP_DIR / "failing_review_roundtrip.csv"),
    )
    assert_condition(failures, passing_completed.returncode == 0, f"Passing CSV evaluation failed: {passing_completed.stderr!r}")
    assert_condition(failures, failing_completed.returncode == 0, f"Failing CSV evaluation failed: {failing_completed.stderr!r}")
    passing_cli = load_json(passing_packet).get("acceptance_result", {}) if passing_packet.exists() else {}
    failing_cli = load_json(failing_packet).get("acceptance_result", {}) if failing_packet.exists() else {}
    assert_condition(failures, passing_cli.get("status") == "accepted_for_next_iteration", f"Passing CSV should evaluate accepted: {passing_cli}")
    assert_condition(failures, failing_cli.get("status") == "not_accepted", f"Failing CSV should evaluate not accepted: {failing_cli}")
    return {"passing": passing_result, "failing": failing_result, "passing_cli": passing_cli, "failing_cli": failing_cli}


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# LIVE-DEMO-003 Supervised Live Voice Acceptance Validator",
        "",
        f"- Passed: `{str(payload['passed']).lower()}`",
        f"- Failure count: `{payload['failure_count']}`",
        f"- Provider calls made: `{str(payload['provider_calls_made']).lower()}`",
        f"- Default acceptance status: `{payload['default_acceptance_status']}`",
        "",
        "## Failures",
        "",
    ]
    lines.extend([f"- {failure}" for failure in payload["failures"]] or ["- None"])
    lines.extend(["", "## Boundary", ""])
    lines.extend(
        [
            "- This validator does not run live voice, browser ASR, or provider TTS.",
            "- It validates the review packet/report shape and default provider-off boundary.",
            "- Tarik still has to run the supervised live voice pass manually.",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    failures: list[str] = []
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    sample_packet = TMP_DIR / "acceptance_packet.json"
    sample_report = TMP_DIR / "acceptance_report.md"

    assert_condition(failures, ACCEPTANCE_SCRIPT.exists(), f"Missing acceptance generator: {ACCEPTANCE_SCRIPT}")
    if not ACCEPTANCE_SCRIPT.exists():
        payload = {
            "checkpoint_id": CHECKPOINT_ID,
            "passed": False,
            "failure_count": len(failures),
            "failures": failures,
            "provider_calls_made": False,
            "default_acceptance_status": "missing_tool",
        }
        GENERATED_DIR.mkdir(parents=True, exist_ok=True)
        RESULT_OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        REPORT_OUT.write_text(render_report(payload), encoding="utf-8")
        raise AssertionError("\n".join(failures))

    completed = run_acceptance_tool(
        "--out",
        str(sample_packet),
        "--report-out",
        str(sample_report),
        "--review-form-out",
        str(SAMPLE_REVIEW_FORM),
        "--review-csv-out",
        str(SAMPLE_REVIEW_CSV),
    )
    assert_condition(
        failures,
        completed.returncode == 0,
        f"Acceptance generator failed. stdout={completed.stdout!r} stderr={completed.stderr!r}",
    )
    packet = load_json(sample_packet) if sample_packet.exists() else {}
    report_text = sample_report.read_text(encoding="utf-8") if sample_report.exists() else ""
    review_form_text = SAMPLE_REVIEW_FORM.read_text(encoding="utf-8") if SAMPLE_REVIEW_FORM.exists() else ""
    review_csv_text = SAMPLE_REVIEW_CSV.read_text(encoding="utf-8") if SAMPLE_REVIEW_CSV.exists() else ""
    validate_schema(packet, report_text, review_form_text, review_csv_text, failures)
    validate_boundaries(packet, failures)
    review_outcomes = validate_review_outcomes(packet, failures) if packet else {}

    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "passed": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "provider_calls_made": False,
        "default_acceptance_status": (packet.get("acceptance_result") or {}).get("status"),
        "review_outcomes": review_outcomes,
        "evidence": {
            "sample_packet_path": str(sample_packet.relative_to(ROOT)) if sample_packet.exists() else None,
            "sample_report_path": str(sample_report.relative_to(ROOT)) if sample_report.exists() else None,
            "sample_review_form_path": str(SAMPLE_REVIEW_FORM.relative_to(ROOT)) if SAMPLE_REVIEW_FORM.exists() else None,
            "sample_review_csv_path": str(SAMPLE_REVIEW_CSV.relative_to(ROOT)) if SAMPLE_REVIEW_CSV.exists() else None,
            "turn_count": len(packet.get("turns", [])) if packet else 0,
        },
    }
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    REPORT_OUT.write_text(render_report(payload), encoding="utf-8")
    if failures:
        raise AssertionError("\n".join(failures))
    print("LIVE-DEMO-003 supervised live voice acceptance validation passed.")


if __name__ == "__main__":
    main()
