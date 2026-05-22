#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core import campaign_playbook_adapter as adapter  # noqa: E402


try:
    from runtime.core import campaign_registry as registry  # noqa: E402
except Exception as exc:  # pragma: no cover - red-test path
    registry = None
    REGISTRY_IMPORT_ERROR = repr(exc)
else:
    REGISTRY_IMPORT_ERROR = None

try:
    from runtime.entrypoints import generic_campaign_turn as entrypoint  # noqa: E402
except Exception as exc:  # pragma: no cover - red-test path
    entrypoint = None
    ENTRYPOINT_IMPORT_ERROR = repr(exc)
else:
    ENTRYPOINT_IMPORT_ERROR = None


CHECKPOINT_ID = "CAMPAIGN-REGISTRY-001"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID

CAMPAIGN_ROOT = ROOT / "runtime" / "campaigns"
README_PATH = CAMPAIGN_ROOT / "README.md"
SCHEMA_PATH = CAMPAIGN_ROOT / "schema" / "campaign_config.schema.json"
EXAMPLE_DIR = CAMPAIGN_ROOT / "examples"

ROUTESIGNAL_PLAYBOOK_ID = "ROUTESIGNAL-DIAGNOSTIC-PLAYBOOK-001"
ROUTESIGNAL_GAP_IDS = {"callbacks", "manual_tracking", "handoffs", "routing", "reminders", "duplicates"}
FORBIDDEN_GENERIC_OUTPUT_TERMS = ["RouteSignal", "Northstar", "Starter", "Growth", "$29", "$59"]
SAFETY_KEYS = [
    "provider_calls_made",
    "local_llm_calls_made",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
]
EXAMPLE_FILES = {
    "insurance": "synthetic-insurance-review.json",
    "telecom": "synthetic-telecom-plan-review.json",
    "home_services": "synthetic-home-services-estimate.json",
    "b2b_saas": "synthetic-b2b-saas-operations.json",
    "healthcare_admin": "synthetic-healthcare-admin-review.json",
    "automotive_service": "synthetic-automotive-service-review.json",
    "membership": "synthetic-membership-plan-review.json",
    "retail_support": "synthetic-retail-support-review.json",
}
CONFIG_PATH_RUNTIME_LABELS = ["insurance", "telecom", "b2b_saas", "home_services"]
CONFIG_PATH_TARGET_GAPS = {
    "insurance": "premium_or_budget",
    "telecom": "coverage_or_availability",
    "b2b_saas": "visibility_gap",
    "home_services": "estimate_or_property_details",
}


def assert_condition(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def normalize(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): sanitize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    return value


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return payload


def write_evidence(result: dict[str, Any], report: str) -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(report, encoding="utf-8")


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


def memory(packet: dict[str, Any]) -> dict[str, Any]:
    return dict(packet.get("demo_conversation_memory") or packet.get("conversation_memory") or {})


def semantic_frame(packet: dict[str, Any]) -> dict[str, Any]:
    manager = packet.get("dialogue_manager") or {}
    selected = manager.get("selected_action") or {}
    frame = selected.get("contextual_buyer_semantics") or selected.get("semantic_frame") or {}
    if frame:
        return frame
    if selected.get("semantic"):
        return selected
    return manager.get("contextual_buyer_semantics") or {}


def final_response(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("final_response") or (packet.get("packet") or {}).get("final_response") or "")


def tts_input_text(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("tts_input_text") or (((packet.get("packet") or {}).get("tts_delivery") or {}).get("tts_input_text")) or "")


def snapshot(packet: dict[str, Any]) -> dict[str, Any]:
    frame = semantic_frame(packet)
    packet_body = packet.get("packet") or {}
    tts = packet_body.get("tts_delivery") or {}
    voice = packet_body.get("voice_delivery") or {}
    manager = packet.get("dialogue_manager") or {}
    lead = memory(packet).get("lead_followup_state") or {}
    return sanitize(
        {
            "transcript": packet.get("transcript"),
            "campaign_id": packet.get("campaign_id"),
            "campaign_playbook_id": packet.get("campaign_playbook_id"),
            "semantic": frame.get("semantic"),
            "target_gap": frame.get("target_gap"),
            "playbook_id": frame.get("playbook_id"),
            "playbook_review_focus": frame.get("playbook_review_focus"),
            "call_control": (packet.get("summary") or {}).get("call_control"),
            "final_response": final_response(packet),
            "tts_input_text": tts_input_text(packet),
            "lead_followup_state": lead,
            "audio_url": packet.get("audio_url"),
            "provider_agent_used": packet.get("provider_agent_used"),
            "durable_provider_agent_created": packet.get("durable_provider_agent_created"),
            "voice_cloning_used": packet.get("voice_cloning_used"),
            "provider_calls_made": bool(tts.get("provider_calls_made") or voice.get("provider_calls_made") or packet_body.get("api_calls_made")),
            "local_llm_calls_made": bool(manager.get("local_llm_calls_made") or packet_body.get("llm_used")),
            "sends_email": bool((lead.get("safety") or {}).get("sends_email")),
            "creates_calendar_event": bool((lead.get("safety") or {}).get("creates_calendar_event")),
            "writes_crm": bool((lead.get("safety") or {}).get("writes_crm")),
            "opens_prod_102": bool(packet.get("opens_prod_102") or manager.get("opens_prod_102")),
        }
    )


def assert_safety(failures: list[str], packet: dict[str, Any], label: str) -> None:
    snap = snapshot(packet)
    for key in SAFETY_KEYS:
        assert_condition(failures, snap.get(key) is False, f"{label}: {key} must be false: {snap}")
    assert_condition(failures, snap.get("provider_agent_used") is False, f"{label}: provider agent must be false: {snap}")
    assert_condition(failures, snap.get("durable_provider_agent_created") is False, f"{label}: durable provider agent must be false: {snap}")
    assert_condition(failures, snap.get("voice_cloning_used") is False, f"{label}: voice cloning must be false: {snap}")
    assert_condition(failures, snap.get("audio_url") in (None, ""), f"{label}: dry-run audio_url must be null/absent: {snap}")


def assert_no_generic_leakage(failures: list[str], packet: dict[str, Any], label: str) -> None:
    texts = {"final_response": final_response(packet), "tts_input_text": tts_input_text(packet)}
    for text_name, text in texts.items():
        found = [term for term in FORBIDDEN_GENERIC_OUTPUT_TERMS if term.lower() in text.lower()]
        assert_condition(failures, not found, f"{label}: {text_name} leaked forbidden generic output terms {found}: {text}")


def validate_schema_and_examples_exist(failures: list[str], evidence: dict[str, Any]) -> None:
    paths = {
        "readme": README_PATH,
        "schema": SCHEMA_PATH,
        **{label: EXAMPLE_DIR / filename for label, filename in EXAMPLE_FILES.items()},
    }
    evidence["schema_and_examples"] = {label: str(path.relative_to(ROOT)) for label, path in paths.items()}
    for label, path in paths.items():
        assert_condition(failures, path.is_file(), f"{label}: expected file missing at {path.relative_to(ROOT)}")


def load_examples_through_registry(failures: list[str], evidence: dict[str, Any]) -> dict[str, dict[str, Any]]:
    loaded: dict[str, dict[str, Any]] = {}
    evidence["registry_import"] = {
        "imported": registry is not None,
        "import_error": REGISTRY_IMPORT_ERROR,
    }
    assert_condition(failures, registry is not None, f"runtime.core.campaign_registry import failed: {REGISTRY_IMPORT_ERROR}")
    if registry is None:
        return loaded

    example_evidence: dict[str, Any] = {}
    for label, filename in EXAMPLE_FILES.items():
        path = EXAMPLE_DIR / filename
        if not path.is_file():
            continue
        try:
            config = registry.load_campaign_config(path)
            validation = registry.validate_campaign_config(config)
            playbook = adapter.resolve_campaign_playbook(config)
            adapter_validation = adapter.validate_campaign_playbook(playbook)
        except Exception as exc:
            failures.append(f"{label}: example failed to load through campaign_registry: {type(exc).__name__}: {exc}")
            continue

        loaded[label] = config
        entry = registry.campaign_registry_entry(config, path)
        example_evidence[label] = {
            "path": str(path.relative_to(ROOT)),
            "campaign_id": config.get("campaign_id"),
            "vertical_id": config.get("vertical_id"),
            "campaign_playbook_id": playbook.get("campaign_playbook_id"),
            "registry_entry": entry,
            "validation": validation,
            "adapter_validation": adapter_validation,
        }
        assert_condition(failures, validation.get("valid") is True, f"{label}: registry validation failed: {validation}")
        assert_condition(failures, adapter_validation.get("valid") is True, f"{label}: adapter validation failed: {adapter_validation}")
        assert_condition(failures, playbook.get("campaign_playbook_id") != ROUTESIGNAL_PLAYBOOK_ID, f"{label}: resolved to RouteSignal")
    evidence["examples_load"] = example_evidence
    return loaded


def build_packet_from_config_path(
    *,
    transcript: str,
    config_path: Path,
    state: dict[str, Any],
    session_id: str,
) -> dict[str, Any]:
    if entrypoint is None:
        raise RuntimeError(f"generic_campaign_turn import failed: {ENTRYPOINT_IMPORT_ERROR}")
    helper = getattr(entrypoint, "build_generic_campaign_turn_packet_from_config_path", None)
    if not callable(helper):
        raise RuntimeError("build_generic_campaign_turn_packet_from_config_path is missing")
    return helper(
        transcript=transcript,
        campaign_config_path=config_path,
        input_type="agent-open" if transcript == "__agent_open__" else "speech-final",
        session_id=session_id,
        session_state=state,
        private_out=TMP_DIR / session_id,
        live_tts=False,
        force_key_missing=True,
        timeout_seconds=8.0,
    )


def positive_phrase_for_runtime(label: str, config: dict[str, Any]) -> tuple[str, str]:
    gap_order = list(config.get("gap_order") or (config.get("diagnostic_gaps") or {}).keys())
    if not gap_order:
        raise AssertionError(f"{config.get('campaign_id')}: gap_order is empty")
    gap_id = CONFIG_PATH_TARGET_GAPS.get(label) or str(gap_order[0])
    gap = (config.get("diagnostic_gaps") or {}).get(gap_id) or {}
    phrases = list(gap.get("evidence_positive") or [])
    if not phrases:
        raise AssertionError(f"{config.get('campaign_id')}.{gap_id}: evidence_positive is empty")
    return gap_id, str(phrases[0])


def run_config_path_sequence(label: str, config_path: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
    target_gap, pain_phrase = positive_phrase_for_runtime(label, config)
    transcripts = ["__agent_open__", "yeah sure", pain_phrase, "tomorrow at 3 works"]
    state: dict[str, Any] = {"turns": []}
    packets: list[dict[str, Any]] = []
    for transcript in transcripts:
        packet = build_packet_from_config_path(
            transcript=transcript,
            config_path=config_path,
            state=state,
            session_id=f"config-path-{label}",
        )
        packets.append(packet)
        append_turn(state, packet)
    return packets


def validate_config_path_runtime(failures: list[str], evidence: dict[str, Any], loaded: dict[str, dict[str, Any]]) -> None:
    assert_condition(failures, entrypoint is not None, f"runtime.entrypoints.generic_campaign_turn import failed: {ENTRYPOINT_IMPORT_ERROR}")
    if entrypoint is None:
        return
    helper = getattr(entrypoint, "build_generic_campaign_turn_packet_from_config_path", None)
    assert_condition(failures, callable(helper), "build_generic_campaign_turn_packet_from_config_path must exist")
    if not callable(helper):
        return

    runtime_evidence: dict[str, Any] = {}
    for label in CONFIG_PATH_RUNTIME_LABELS:
        config = loaded.get(label)
        if not config:
            continue
        config_path = EXAMPLE_DIR / EXAMPLE_FILES[label]
        expected_gap, pain_phrase = positive_phrase_for_runtime(label, config)
        packets = run_config_path_sequence(label, config_path, config)
        runtime_evidence[label] = {
            "config_path": str(config_path.relative_to(ROOT)),
            "pain_phrase": pain_phrase,
            "expected_gap": expected_gap,
            "turns": [snapshot(packet) for packet in packets],
        }
        for index, packet in enumerate(packets, start=1):
            assert_safety(failures, packet, f"{label}_turn{index}")
            assert_no_generic_leakage(failures, packet, f"{label}_turn{index}")
            assert_condition(failures, packet.get("campaign_playbook_id") != ROUTESIGNAL_PLAYBOOK_ID, f"{label}_turn{index}: packet resolved to RouteSignal")
        pain_frame = semantic_frame(packets[2])
        assert_condition(failures, pain_frame.get("target_gap") == expected_gap, f"{label}: target_gap did not come from file config: {snapshot(packets[2])}")
        assert_condition(failures, expected_gap not in ROUTESIGNAL_GAP_IDS, f"{label}: target_gap leaked RouteSignal gap id: {expected_gap}")
        final_lead = memory(packets[3]).get("lead_followup_state") or {}
        appointment = final_lead.get("appointment") or {}
        callback = final_lead.get("callback") or {}
        normalized = callback.get("normalized") or {}
        assert_condition(
            failures,
            appointment.get("confirmed") is True or "3" in str(normalized.get("time_text") or ""),
            f"{label}: appointment/callback time not captured: {snapshot(packets[3])}",
        )
    evidence["config_path_runtime"] = runtime_evidence


def write_invalid_config(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def validate_invalid_config_rejection(failures: list[str], evidence: dict[str, Any], loaded: dict[str, dict[str, Any]]) -> None:
    if registry is None or entrypoint is None or "insurance" not in loaded:
        evidence["invalid_config_rejection"] = {"skipped": True, "reason": "registry, entrypoint, or insurance example unavailable"}
        return

    base = copy.deepcopy(loaded["insurance"])
    first_gap = str((base.get("gap_order") or [next(iter(base.get("diagnostic_gaps") or {}))])[0])
    invalids: dict[str, dict[str, Any]] = {}

    missing_gaps = copy.deepcopy(base)
    missing_gaps.pop("diagnostic_gaps", None)
    invalids["missing_diagnostic_gaps"] = missing_gaps

    unsupported_vertical = copy.deepcopy(base)
    unsupported_vertical["vertical_id"] = "unsupported_vertical"
    invalids["unsupported_vertical_id"] = unsupported_vertical

    unknown_pain = copy.deepcopy(base)
    unknown_pain["diagnostic_gaps"][first_gap]["universal_pain_dimensions"] = ["not_a_real_pain_dimension"]
    invalids["unknown_universal_pain_dimension"] = unknown_pain

    missing_blocked = copy.deepcopy(base)
    missing_blocked.pop("blocked_claims", None)
    invalids["missing_blocked_claims_regulated"] = missing_blocked

    missing_target = copy.deepcopy(base)
    missing_target.pop("appointment_target", None)
    invalids["missing_appointment_target"] = missing_target

    missing_owner = copy.deepcopy(base)
    missing_owner.pop("human_followup_owner", None)
    invalids["missing_human_followup_owner"] = missing_owner

    invalid_evidence: dict[str, Any] = {}
    for label, payload in invalids.items():
        path = TMP_DIR / "invalid-configs" / f"{label}.json"
        write_invalid_config(path, payload)
        record: dict[str, Any] = {"path": str(path.relative_to(ROOT))}
        try:
            loaded_config = registry.load_campaign_config(path)
        except Exception as exc:
            message = str(exc)
            record["load_error"] = {"type": type(exc).__name__, "message": message}
            assert_condition(failures, ROUTESIGNAL_PLAYBOOK_ID not in message, f"{label}: validation error leaked RouteSignal playbook id: {message}")
            assert_condition(failures, "routesignal" not in message.lower(), f"{label}: validation error leaked RouteSignal wording: {message}")
        else:
            validation = registry.validate_campaign_config(loaded_config)
            record["validation"] = validation
            assert_condition(failures, validation.get("valid") is False, f"{label}: invalid config validated cleanly: {validation}")

        try:
            build_packet_from_config_path(
                transcript="__agent_open__",
                config_path=path,
                state={"turns": []},
                session_id=f"invalid-{label}",
            )
        except Exception as exc:
            message = str(exc)
            record["runtime_error"] = {"type": type(exc).__name__, "message": message}
            assert_condition(failures, ROUTESIGNAL_PLAYBOOK_ID not in message, f"{label}: runtime error leaked RouteSignal playbook id: {message}")
            assert_condition(failures, "routesignal" not in message.lower(), f"{label}: runtime error leaked RouteSignal wording: {message}")
        else:
            failures.append(f"{label}: config-path runtime generated a packet for an invalid config")
        invalid_evidence[label] = record
    evidence["invalid_config_rejection"] = invalid_evidence


def validate_registry_listing(failures: list[str], evidence: dict[str, Any]) -> None:
    if registry is None:
        return
    try:
        entries = registry.list_campaign_configs()
    except Exception as exc:
        failures.append(f"list_campaign_configs failed: {type(exc).__name__}: {exc}")
        return

    by_campaign_id = {str(entry.get("campaign_id")): entry for entry in entries}
    evidence["registry_listing"] = entries
    assert_condition(failures, len(entries) >= len(EXAMPLE_FILES), f"registry listing returned too few entries: {len(entries)}")
    for label, filename in EXAMPLE_FILES.items():
        path = EXAMPLE_DIR / filename
        campaign_id = load_json(path).get("campaign_id") if path.is_file() else None
        entry = by_campaign_id.get(str(campaign_id))
        assert_condition(failures, isinstance(entry, dict), f"{label}: registry entry missing for {campaign_id}")
        if not isinstance(entry, dict):
            continue
        for key in ["campaign_id", "vertical_id", "product_or_offer_name", "appointment_target", "path", "validation_status"]:
            assert_condition(failures, key in entry and entry.get(key) not in (None, ""), f"{label}: registry entry missing {key}: {entry}")
        assert_condition(failures, entry.get("validation_status") == "valid", f"{label}: registry entry status must be valid: {entry}")


def validate_routesignal_preservation(failures: list[str], evidence: dict[str, Any]) -> None:
    from scripts.run_live_demo_001_agent_voice_call import (  # noqa: E402
        DEFAULT_CAMPAIGN_ID,
        DEFAULT_CASES_PATH,
        DEFAULT_STAGE,
        build_turn_packet,
    )

    state: dict[str, Any] = {"turns": []}
    packets: list[dict[str, Any]] = []
    for transcript in ["__agent_open__", "yeah sure", "callbacks are fine"]:
        packet = build_turn_packet(
            transcript=transcript,
            campaign_id=DEFAULT_CAMPAIGN_ID,
            stage=DEFAULT_STAGE,
            input_type="agent-open" if transcript == "__agent_open__" else "speech-final",
            silence_count=0,
            cases_path=DEFAULT_CASES_PATH,
            private_out=TMP_DIR / "routesignal",
            live_tts=False,
            force_key_missing=True,
            timeout_seconds=8.0,
            session_id="campaign-registry-routesignal",
            session_state=state,
            asr_confidence=0.94,
            voice_turn_state="listening",
        )
        packets.append(packet)
        append_turn(state, packet)
    evidence["routesignal_preservation"] = [snapshot(packet) for packet in packets]
    final = evidence["routesignal_preservation"][-1]
    assert_condition(failures, final.get("semantic") == "current_gap_clear", f"RouteSignal semantic changed: {final}")
    assert_condition(failures, final.get("target_gap") == "callbacks", f"RouteSignal target_gap changed: {final}")
    assert_condition(failures, final.get("playbook_id") == ROUTESIGNAL_PLAYBOOK_ID, f"RouteSignal playbook changed: {final}")


def assert_no_private_or_side_effect_evidence(failures: list[str], result: dict[str, Any]) -> None:
    serialized = json.dumps(result, sort_keys=True).lower()
    forbidden = ["data/private", "private transcript", "raw private", "generated audio"]
    found = [term for term in forbidden if term in serialized]
    assert_condition(failures, not found, f"generated evidence contains forbidden private/audio wording: {found}")
    for key in SAFETY_KEYS:
        assert_condition(failures, (result.get("safety_assertions") or {}).get(key) is False, f"result safety {key} must be false")


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# CAMPAIGN-REGISTRY-001",
        "",
        f"Status: {result['status']}",
        f"Failure count: {len(result.get('failures') or [])}",
        "",
        "## Contract",
        "",
        "- File-backed synthetic campaign configs load through `runtime.core.campaign_registry`.",
        "- Invalid generic campaign configs fail locally and do not fall back to RouteSignal.",
        "- Generic config-path runtime helper preserves in-memory campaign behavior and keeps live TTS/provider side effects off.",
        "- RouteSignal live-demo path remains unchanged.",
        "",
        "## Files",
        "",
        f"- Schema: `{SCHEMA_PATH.relative_to(ROOT)}`",
        f"- Examples: `{EXAMPLE_DIR.relative_to(ROOT)}`",
        "",
        "## Failures",
        "",
    ]
    failures = result.get("failures") or []
    if failures:
        lines.extend(f"- {failure}" for failure in failures)
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def main() -> int:
    failures: list[str] = []
    evidence: dict[str, Any] = {}

    validate_schema_and_examples_exist(failures, evidence)
    loaded = load_examples_through_registry(failures, evidence)
    validate_config_path_runtime(failures, evidence, loaded)
    validate_invalid_config_rejection(failures, evidence, loaded)
    validate_registry_listing(failures, evidence)
    validate_routesignal_preservation(failures, evidence)

    result = sanitize(
        {
            "checkpoint_id": CHECKPOINT_ID,
            "status": "pass" if not failures else "fail",
            "failures": failures,
            "evidence": evidence,
            "forbidden_terms_checked": FORBIDDEN_GENERIC_OUTPUT_TERMS,
            "routesignal_playbook_id": ROUTESIGNAL_PLAYBOOK_ID,
            "safety_assertions": {key: False for key in SAFETY_KEYS},
            "provider_calls_made": False,
            "local_llm_calls_made": False,
            "sends_email": False,
            "creates_calendar_event": False,
            "writes_crm": False,
            "opens_prod_102": False,
            "uses_provider_calls": False,
            "uses_live_tts": False,
            "uses_real_customer_data": False,
            "uses_private_transcripts": False,
            "uses_generated_audio": False,
            "runtime_behavior_changed": False,
        }
    )
    assert_no_private_or_side_effect_evidence(failures, result)
    result["failures"] = failures
    result["status"] = "pass" if not failures else "fail"
    write_evidence(result, render_report(result))
    if failures:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1
    print(f"{CHECKPOINT_ID}: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
