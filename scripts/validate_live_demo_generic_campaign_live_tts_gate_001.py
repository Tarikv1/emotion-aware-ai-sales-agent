#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import run_live_demo_001_agent_voice_call as demo  # noqa: E402


CHECKPOINT_ID = "LIVE-DEMO-GENERIC-CAMPAIGN-LIVE-TTS-GATE-001"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID
RUNNER = ROOT / "scripts" / "run_live_demo_001_agent_voice_call.py"
INSURANCE_CONFIG = ROOT / "runtime" / "campaigns" / "examples" / "synthetic-insurance-review.json"
ROUTESIGNAL_PLAYBOOK_ID = "ROUTESIGNAL-DIAGNOSTIC-PLAYBOOK-001"
GATE_ERROR = "--campaign-config with --live-tts requires --allow-generic-live-tts. Generic campaign provider audio is explicitly gated."
DRY_RUN_WARNING = "Generic campaign configs run dry-run TTS by default. No provider calls are made."
LIVE_TTS_WARNING = (
    "Generic campaign live TTS is enabled. Generated agent text may be sent to ElevenLabs. "
    "Customer audio is not sent to Python or the TTS provider."
)
REAL_LIVE_TTS_COMMAND = (
    "python scripts\\run_live_demo_001_agent_voice_call.py "
    "--campaign-config runtime/campaigns/examples/synthetic-insurance-review.json "
    "--live-tts --consent-confirmed --allow-generic-live-tts"
)
SAFETY_KEYS = [
    "provider_calls_made",
    "local_llm_calls_made",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
]


def assert_condition(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def write_evidence(result: dict[str, Any], report: str) -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(report, encoding="utf-8")


def make_args(
    *,
    campaign_config: str | None = None,
    live_tts: bool = False,
    force_key_missing: bool = True,
    consent_confirmed: bool = False,
    allow_generic_live_tts: bool = False,
) -> argparse.Namespace:
    return argparse.Namespace(
        host=demo.DEFAULT_HOST,
        port=0,
        campaign=demo.DEFAULT_CAMPAIGN_ID,
        campaign_config=campaign_config,
        stage=demo.DEFAULT_STAGE,
        live_tts=live_tts,
        force_key_missing=force_key_missing,
        timeout_seconds=8.0,
        consent_confirmed=consent_confirmed,
        allow_generic_live_tts=allow_generic_live_tts,
        live_tts_preflight={"api_key_present": False, "voice_id_present": False, "voice_id_source": None},
        live_tts_env_file_status={"path": None, "present": False, "loaded_keys": [], "ignored_keys": []},
    )


def append_turn(state: dict[str, Any], packet: dict[str, Any]) -> None:
    state.setdefault("turns", []).append(
        {
            "transcript": packet.get("transcript", ""),
            "summary": packet.get("summary", {}),
            "continuity": packet.get("demo_session_continuity") or packet.get("conversation_continuity") or {},
            "conversation_memory": packet.get("demo_conversation_memory") or packet.get("conversation_memory") or {},
            "dialogue_manager": packet.get("dialogue_manager", {}),
            "dialogue_pragmatics": packet.get("dialogue_pragmatics", {}),
        }
    )


def semantic_frame(packet: dict[str, Any]) -> dict[str, Any]:
    manager = packet.get("dialogue_manager") or {}
    selected = manager.get("selected_action") or {}
    frame = selected.get("contextual_buyer_semantics") or selected.get("semantic_frame") or {}
    if frame:
        return frame
    if selected.get("semantic"):
        return selected
    return manager.get("contextual_buyer_semantics") or {}


def snapshot(packet: dict[str, Any]) -> dict[str, Any]:
    packet_body = packet.get("packet") or {}
    tts = packet_body.get("tts_delivery") or {}
    asr = packet.get("asr") or {}
    manager = packet.get("dialogue_manager") or {}
    memory = packet.get("demo_conversation_memory") or packet.get("conversation_memory") or {}
    lead = memory.get("lead_followup_state") or {}
    summary = packet.get("summary") or {}
    frame = semantic_frame(packet)
    selected = packet.get("selected_campaign_config") or {}
    return {
        "mode": packet.get("mode"),
        "campaign_selector_mode": packet.get("campaign_selector_mode"),
        "campaign_config_path": packet.get("campaign_config_path"),
        "selected_campaign_config": selected,
        "campaign_id": packet.get("campaign_id"),
        "campaign_playbook_id": packet.get("campaign_playbook_id"),
        "vertical_id": packet.get("vertical_id") or selected.get("vertical_id"),
        "semantic": frame.get("semantic"),
        "target_gap": frame.get("target_gap"),
        "playbook_id": frame.get("playbook_id"),
        "final_response": summary.get("final_response"),
        "audio_url": packet.get("audio_url"),
        "provider_calls_made": packet.get("provider_calls_made"),
        "local_llm_calls_made": packet.get("local_llm_calls_made"),
        "sends_email": packet.get("sends_email"),
        "creates_calendar_event": packet.get("creates_calendar_event"),
        "writes_crm": packet.get("writes_crm"),
        "opens_prod_102": packet.get("opens_prod_102"),
        "live_tts_used": packet.get("live_tts_used"),
        "tts_provider_calls_made": packet.get("tts_provider_calls_made"),
        "audio_file_created": packet.get("audio_file_created"),
        "customer_audio_uploaded_to_python_server": packet.get("customer_audio_uploaded_to_python_server"),
        "customer_audio_uploaded_to_tts_provider": packet.get("customer_audio_uploaded_to_tts_provider"),
        "tts_live_call_requested": tts.get("live_call_requested"),
        "tts_fallback_reason": tts.get("fallback_reason") or summary.get("tts_fallback_reason"),
        "tts_generated_text_sent_to_provider": tts.get("generated_text_sent_to_provider"),
        "asr_audio_uploaded_to_python_server": asr.get("audio_uploaded_to_python_server"),
        "selected_live_tts_enabled": selected.get("live_tts_enabled"),
        "generic_selected_campaign_live_tts_allowed": packet.get("generic_selected_campaign_live_tts_allowed"),
        "call_control": summary.get("call_control"),
    }


def assert_no_side_effects(failures: list[str], snap: dict[str, Any], label: str) -> None:
    for key in SAFETY_KEYS:
        assert_condition(failures, snap.get(key) is False, f"{label}: {key} must be false: {snap}")
    assert_condition(failures, snap.get("customer_audio_uploaded_to_python_server") is False, f"{label}: customer audio uploaded to python: {snap}")
    assert_condition(failures, snap.get("customer_audio_uploaded_to_tts_provider") is False, f"{label}: customer audio uploaded to tts provider: {snap}")


def run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(RUNNER), *args], cwd=ROOT, text=True, capture_output=True)


def parse_stdout_json(completed: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Expected JSON stdout, got: {completed.stdout!r}\nstderr: {completed.stderr!r}") from exc


def build_turn(
    *,
    transcript: str,
    state: dict[str, Any],
    session_id: str,
    campaign_config_path: Path | None = None,
    live_tts: bool = False,
    force_key_missing: bool = True,
    generic_live_tts_allowed: bool = False,
) -> dict[str, Any]:
    packet = demo.build_browser_demo_turn_packet(
        transcript=transcript,
        campaign_id=demo.DEFAULT_CAMPAIGN_ID,
        campaign_config_path=campaign_config_path,
        stage=demo.DEFAULT_STAGE,
        input_type="agent-open" if transcript == "__agent_open__" else "speech-final",
        silence_count=0,
        cases_path=demo.DEFAULT_CASES_PATH,
        private_out=TMP_DIR / session_id,
        live_tts=live_tts,
        force_key_missing=force_key_missing,
        timeout_seconds=8.0,
        session_id=session_id,
        session_state=state,
        asr_confidence=0.94,
        voice_turn_state="listening",
        generic_live_tts_allowed=generic_live_tts_allowed,
    )
    append_turn(state, packet)
    return packet


def validate_default_generic_dry_run(failures: list[str], evidence: dict[str, Any]) -> None:
    state: dict[str, Any] = {"turns": []}
    packet = build_turn(
        transcript="premium is a problem",
        state=state,
        session_id="default-generic-dry-run",
        campaign_config_path=INSURANCE_CONFIG,
        live_tts=False,
        force_key_missing=True,
        generic_live_tts_allowed=False,
    )
    snap = snapshot(packet)
    evidence["default_generic_dry_run"] = snap
    assert_condition(failures, snap["campaign_selector_mode"] == "generic_config", f"default generic selector wrong: {snap}")
    assert_condition(failures, snap["mode"] == "dry-run", f"default generic mode should be dry-run: {snap}")
    assert_condition(failures, snap["selected_live_tts_enabled"] is False, f"default generic live_tts_enabled should be false: {snap}")
    assert_condition(failures, snap["provider_calls_made"] is False, f"default generic provider call changed: {snap}")
    assert_condition(failures, snap["tts_provider_calls_made"] is False, f"default generic tts provider call changed: {snap}")
    assert_condition(failures, snap["live_tts_used"] is False, f"default generic live_tts_used should be false: {snap}")
    assert_condition(failures, snap["audio_url"] in (None, ""), f"default generic audio_url should be null: {snap}")
    assert_no_side_effects(failures, snap, "default generic dry-run")


def validate_cli_blocked_without_gate(failures: list[str], evidence: dict[str, Any]) -> None:
    completed = run_cli(
        [
            "--campaign-config",
            "runtime/campaigns/examples/synthetic-insurance-review.json",
            "--live-tts",
            "--consent-confirmed",
            "--decision-transcript",
            "premium is a problem",
            "--private-out",
            str(TMP_DIR / "blocked-private"),
        ]
    )
    combined = f"{completed.stdout}\n{completed.stderr}"
    evidence["blocked_without_gate"] = {
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "expected_error_present": GATE_ERROR in combined,
    }
    assert_condition(failures, completed.returncode != 0, f"CLI should fail without generic live TTS gate: {completed.stdout}")
    assert_condition(failures, GATE_ERROR in combined, f"CLI missing gate error. Got: {combined}")
    assert_condition(failures, "RouteSignal" not in combined, f"blocked generic TTS should not fall back to RouteSignal: {combined}")


def validate_cli_allowed_forced_missing(failures: list[str], evidence: dict[str, Any]) -> None:
    completed = run_cli(
        [
            "--campaign-config",
            "runtime/campaigns/examples/synthetic-insurance-review.json",
            "--live-tts",
            "--consent-confirmed",
            "--allow-generic-live-tts",
            "--force-key-missing",
            "--decision-transcript",
            "premium is a problem",
            "--private-out",
            str(TMP_DIR / "allowed-missing-private"),
        ]
    )
    evidence["allowed_forced_missing_cli"] = {
        "returncode": completed.returncode,
        "stderr": completed.stderr.strip(),
    }
    assert_condition(failures, completed.returncode == 0, f"allowed forced-missing CLI failed: {completed.stderr}\n{completed.stdout}")
    if completed.returncode != 0:
        return
    packet = parse_stdout_json(completed)
    snap = snapshot(packet)
    evidence["allowed_forced_missing_cli"]["snapshot"] = snap
    assert_condition(failures, snap["campaign_selector_mode"] == "generic_config", f"allowed CLI selector wrong: {snap}")
    assert_condition(failures, snap["campaign_id"] == "synthetic-insurance-review", f"allowed CLI campaign wrong: {snap}")
    assert_condition(failures, snap["selected_live_tts_enabled"] is True, f"allowed CLI selected live_tts_enabled should be true: {snap}")
    assert_condition(failures, snap["generic_selected_campaign_live_tts_allowed"] is True, f"allowed CLI live gate trace missing: {snap}")
    assert_condition(failures, snap["mode"] == "live-tts", f"allowed CLI should request live-tts mode with forced missing key: {snap}")
    assert_condition(failures, snap["tts_live_call_requested"] is True, f"allowed CLI live call request missing: {snap}")
    assert_condition(failures, snap["tts_fallback_reason"] == "forced-key-missing", f"allowed CLI fallback reason wrong: {snap}")
    assert_condition(failures, snap["provider_calls_made"] is False, f"allowed forced missing must not call provider: {snap}")
    assert_condition(failures, snap["tts_provider_calls_made"] is False, f"allowed forced missing TTS call must be false: {snap}")
    assert_condition(failures, snap["audio_file_created"] is False, f"allowed forced missing must not create audio: {snap}")
    assert_condition(failures, snap["audio_url"] in (None, ""), f"allowed forced missing audio_url must be null: {snap}")
    assert_no_side_effects(failures, snap, "allowed forced missing")


def validate_metadata_gate_visibility(failures: list[str], evidence: dict[str, Any]) -> None:
    default_metadata = demo.build_metadata(make_args(), demo.DEFAULT_CASES_PATH, TMP_DIR / "metadata-default")
    dry_metadata = demo.build_metadata(
        make_args(campaign_config="runtime/campaigns/examples/synthetic-insurance-review.json"),
        demo.DEFAULT_CASES_PATH,
        TMP_DIR / "metadata-dry",
    )
    live_metadata = demo.build_metadata(
        make_args(
            campaign_config="runtime/campaigns/examples/synthetic-insurance-review.json",
            live_tts=True,
            force_key_missing=True,
            consent_confirmed=True,
            allow_generic_live_tts=True,
        ),
        demo.DEFAULT_CASES_PATH,
        TMP_DIR / "metadata-live",
    )
    evidence["metadata_gate_visibility"] = {
        "default": {
            "generic_campaigns_live_tts_enabled_by_default": default_metadata.get("generic_campaigns_live_tts_enabled_by_default"),
            "generic_selected_campaign_live_tts_allowed": default_metadata.get("generic_selected_campaign_live_tts_allowed"),
            "selector": default_metadata.get("campaign_selector"),
        },
        "dry": {
            "default_campaign_config_path": dry_metadata.get("default_campaign_config_path"),
            "generic_selected_campaign_live_tts_allowed": dry_metadata.get("generic_selected_campaign_live_tts_allowed"),
            "selector": dry_metadata.get("campaign_selector"),
        },
        "live": {
            "default_campaign_config_path": live_metadata.get("default_campaign_config_path"),
            "generic_selected_campaign_live_tts_allowed": live_metadata.get("generic_selected_campaign_live_tts_allowed"),
            "selector": live_metadata.get("campaign_selector"),
        },
    }
    for label, metadata in [("default", default_metadata), ("dry", dry_metadata), ("live", live_metadata)]:
        assert_condition(failures, metadata.get("generic_campaigns_live_tts_enabled_by_default") is False, f"{label}: default generic live TTS must be false")
        assert_condition(failures, (metadata.get("campaign_selector") or {}).get("generic_campaigns_live_tts_enabled_by_default") is False, f"{label}: selector default generic live TTS must be false")
        assert_condition(failures, (metadata.get("tts") or {}).get("customer_audio_uploaded_to_python_server") is False, f"{label}: python audio boundary missing")
        assert_condition(failures, (metadata.get("tts") or {}).get("customer_audio_uploaded_to_tts_provider") is False, f"{label}: TTS audio boundary missing")
    assert_condition(failures, default_metadata.get("generic_selected_campaign_live_tts_allowed") is False, f"default metadata live gate should be false: {default_metadata}")
    assert_condition(failures, dry_metadata.get("generic_selected_campaign_live_tts_allowed") is False, f"dry metadata live gate should be false: {dry_metadata}")
    assert_condition(failures, live_metadata.get("generic_selected_campaign_live_tts_allowed") is True, f"live metadata live gate should be true: {live_metadata}")
    assert_condition(failures, (live_metadata.get("campaign_selector") or {}).get("generic_selected_campaign_live_tts_allowed") is True, f"selector live gate missing: {live_metadata.get('campaign_selector')}")
    live_options = live_metadata.get("generic_campaign_options") or []
    selected = next((item for item in live_options if item.get("config_path") == "runtime/campaigns/examples/synthetic-insurance-review.json"), {})
    assert_condition(failures, selected.get("live_tts_enabled") is True, f"selected metadata option should expose live_tts_enabled true: {selected}")
    dry_options = dry_metadata.get("generic_campaign_options") or []
    dry_selected = next((item for item in dry_options if item.get("config_path") == "runtime/campaigns/examples/synthetic-insurance-review.json"), {})
    assert_condition(failures, dry_selected.get("live_tts_enabled") is False, f"dry selected metadata option should expose live_tts_enabled false: {dry_selected}")


def validate_browser_html_warnings(failures: list[str], evidence: dict[str, Any]) -> None:
    metadata = demo.build_metadata(
        make_args(
            campaign_config="runtime/campaigns/examples/synthetic-insurance-review.json",
            live_tts=True,
            force_key_missing=True,
            consent_confirmed=True,
            allow_generic_live_tts=True,
        ),
        demo.DEFAULT_CASES_PATH,
        TMP_DIR / "html-live",
    )
    html = demo.render_html(metadata)
    checks = {
        "dry_run_warning": DRY_RUN_WARNING in html,
        "live_tts_warning": LIVE_TTS_WARNING in html,
        "live_tts_warning_element": "genericCampaignLiveTtsWarning" in html,
        "provider_boundary_fields": "tts_provider_calls_made" in html and "audio_file_created" in html,
        "selected_live_tts_display": "live_tts_enabled" in html,
        "customer_audio_boundary": "Customer audio is not sent to Python or the TTS provider." in html
        and "customer_audio_uploaded_to_python_server" in html
        and "customer_audio_uploaded_to_tts_provider" in html,
    }
    evidence["html_warning_checks"] = checks
    for key, value in checks.items():
        assert_condition(failures, value is True, f"HTML gate warning check failed: {key}")


def validate_routesignal_preservation(failures: list[str], evidence: dict[str, Any]) -> None:
    state: dict[str, Any] = {"turns": []}
    packets = [
        build_turn(transcript="__agent_open__", state=state, session_id="routesignal-preservation", campaign_config_path=None),
        build_turn(transcript="yeah sure", state=state, session_id="routesignal-preservation", campaign_config_path=None),
        build_turn(transcript="callbacks are fine", state=state, session_id="routesignal-preservation", campaign_config_path=None),
    ]
    snaps = [snapshot(packet) for packet in packets]
    evidence["routesignal_preservation"] = snaps
    final = snaps[-1]
    assert_condition(failures, final["campaign_selector_mode"] == "routesignal_live_demo", f"RouteSignal selector changed: {final}")
    assert_condition(failures, final["playbook_id"] == ROUTESIGNAL_PLAYBOOK_ID, f"RouteSignal playbook changed: {final}")
    assert_condition(failures, final["semantic"] == "current_gap_clear", f"RouteSignal semantic changed: {final}")
    assert_condition(failures, final["target_gap"] == "callbacks", f"RouteSignal target gap changed: {final}")
    for index, snap in enumerate(snaps, start=1):
        assert_no_side_effects(failures, snap, f"RouteSignal turn {index}")


def validate_selected_generic_live_gated_forced_missing(failures: list[str], evidence: dict[str, Any]) -> None:
    state: dict[str, Any] = {"turns": []}
    packets = [
        build_turn(
            transcript="__agent_open__",
            state=state,
            session_id="generic-live-gated",
            campaign_config_path=INSURANCE_CONFIG,
            live_tts=True,
            force_key_missing=True,
            generic_live_tts_allowed=True,
        ),
        build_turn(
            transcript="yes sure",
            state=state,
            session_id="generic-live-gated",
            campaign_config_path=INSURANCE_CONFIG,
            live_tts=True,
            force_key_missing=True,
            generic_live_tts_allowed=True,
        ),
        build_turn(
            transcript="premium is a problem",
            state=state,
            session_id="generic-live-gated",
            campaign_config_path=INSURANCE_CONFIG,
            live_tts=True,
            force_key_missing=True,
            generic_live_tts_allowed=True,
        ),
    ]
    snaps = [snapshot(packet) for packet in packets]
    evidence["generic_selected_live_gated_forced_missing"] = snaps
    final = snaps[-1]
    assert_condition(failures, final["campaign_selector_mode"] == "generic_config", f"generic live gated selector wrong: {final}")
    assert_condition(failures, final["campaign_id"] == "synthetic-insurance-review", f"generic live gated campaign wrong: {final}")
    assert_condition(failures, final["campaign_playbook_id"] == "synthetic-insurance-review-playbook", f"generic live gated playbook wrong: {final}")
    assert_condition(failures, final["target_gap"] == "premium_or_budget", f"generic live gated target gap wrong: {final}")
    assert_condition(failures, final["selected_live_tts_enabled"] is True, f"selected config live_tts_enabled missing: {final}")
    assert_condition(failures, final["generic_selected_campaign_live_tts_allowed"] is True, f"generic live gate missing: {final}")
    assert_condition(failures, final["mode"] == "live-tts", f"generic live gated mode should be live-tts: {final}")
    assert_condition(failures, final["tts_live_call_requested"] is True, f"generic live gated request missing: {final}")
    assert_condition(failures, final["tts_fallback_reason"] == "forced-key-missing", f"generic live gated fallback reason wrong: {final}")
    assert_condition(failures, final["provider_calls_made"] is False, f"generic live gated forced missing provider call: {final}")
    assert_condition(failures, final["tts_provider_calls_made"] is False, f"generic live gated forced missing TTS call: {final}")
    assert_condition(failures, final["live_tts_used"] is False, f"generic live gated forced missing should not use live TTS: {final}")
    assert_condition(failures, final["audio_file_created"] is False, f"generic live gated forced missing audio file: {final}")
    for index, snap in enumerate(snaps, start=1):
        assert_no_side_effects(failures, snap, f"generic live gated turn {index}")


def run_scenario(
    label: str,
    failures: list[str],
    evidence: dict[str, Any],
    fn: Callable[[list[str], dict[str, Any]], None],
) -> None:
    before = len(failures)
    try:
        fn(failures, evidence)
    except Exception as exc:  # noqa: BLE001 - validator should record controlled scenario failures.
        failures.append(f"{label}: raised {type(exc).__name__}: {exc}")
    evidence.setdefault("scenario_status", {})[label] = "passed" if len(failures) == before else "failed"


def render_report(result: dict[str, Any]) -> str:
    statuses = result.get("scenario_status") or {}
    lines = [
        f"# {CHECKPOINT_ID}",
        "",
        f"- Default generic dry-run: `{statuses.get('default_generic_dry_run')}`",
        f"- Blocked without explicit gate: `{statuses.get('blocked_without_gate')}`",
        f"- Allowed with forced missing key: `{statuses.get('allowed_forced_missing')}`",
        f"- Metadata gate visibility: `{statuses.get('metadata_gate_visibility')}`",
        f"- Browser HTML warnings: `{statuses.get('browser_html_warnings')}`",
        f"- RouteSignal preservation: `{statuses.get('routesignal_preservation')}`",
        f"- Generic selected live-gated forced missing: `{statuses.get('generic_selected_live_gated_forced_missing')}`",
        f"- Provider calls made: `{str(result.get('provider_calls_made')).lower()}`",
        f"- Customer audio sent to Python: `{str(result.get('customer_audio_uploaded_to_python_server')).lower()}`",
        f"- Customer audio sent to TTS provider: `{str(result.get('customer_audio_uploaded_to_tts_provider')).lower()}`",
        "",
        "## Real Generic Insurance Live TTS Command",
        "",
        "Run only after confirming ElevenLabs env/voice configuration and provider approval:",
        "",
        f"`{REAL_LIVE_TTS_COMMAND}`",
        "",
        "## Failures",
        "",
    ]
    failures = result.get("failures") or []
    lines.extend([f"- {failure}" for failure in failures] or ["- None"])
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    evidence: dict[str, Any] = {
        "checkpoint_id": CHECKPOINT_ID,
        "real_generic_insurance_live_tts_command": REAL_LIVE_TTS_COMMAND,
    }

    run_scenario("default_generic_dry_run", failures, evidence, validate_default_generic_dry_run)
    run_scenario("blocked_without_gate", failures, evidence, validate_cli_blocked_without_gate)
    run_scenario("allowed_forced_missing", failures, evidence, validate_cli_allowed_forced_missing)
    run_scenario("metadata_gate_visibility", failures, evidence, validate_metadata_gate_visibility)
    run_scenario("browser_html_warnings", failures, evidence, validate_browser_html_warnings)
    run_scenario("routesignal_preservation", failures, evidence, validate_routesignal_preservation)
    run_scenario("generic_selected_live_gated_forced_missing", failures, evidence, validate_selected_generic_live_gated_forced_missing)

    payload_text = json.dumps(evidence, ensure_ascii=False)
    evidence["provider_calls_made"] = '"provider_calls_made": true' in payload_text
    evidence["customer_audio_uploaded_to_python_server"] = '"customer_audio_uploaded_to_python_server": true' in payload_text
    evidence["customer_audio_uploaded_to_tts_provider"] = '"customer_audio_uploaded_to_tts_provider": true' in payload_text
    evidence["failures"] = failures
    evidence["passed"] = not failures
    write_evidence(evidence, render_report(evidence))

    if failures:
        raise SystemExit("\n".join(failures))
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
