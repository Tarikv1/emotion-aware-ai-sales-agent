#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.entrypoints import generic_campaign_turn  # noqa: E402
from scripts.validate_generic_campaign_runtime_entrypoint_001 import (  # noqa: E402
    RAW_EMAILS,
    append_turn,
    assert_condition,
    final_response,
    memory,
    sanitize,
    snapshot,
    validate_routesignal_preservation,
)
from scripts.validate_generic_campaign_runtime_regression_001 import synthetic_campaigns  # noqa: E402


CHECKPOINT_ID = "GENERIC-CAMPAIGN-FALLBACK-LEAKAGE-001"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID

ROUTESIGNAL_PLAYBOOK_ID = "ROUTESIGNAL-DIAGNOSTIC-PLAYBOOK-001"
TARGET_VERTICALS = [
    "b2b_saas",
    "insurance",
    "telecom",
    "home_services",
    "healthcare_admin_or_medical_equipment",
    "automotive_service",
    "membership_or_subscription",
    "retail_or_ecommerce_support_sales",
]
FORBIDDEN_TERMS = [
    "RouteSignal",
    "Northstar",
    "Starter",
    "Growth",
    "$29",
    "$59",
    "inbound demo",
    "demo follow-up",
    "missed callbacks",
    "manual tracking",
    "messy handoffs",
    "workflow review with Northstar",
]
SAFETY_KEYS = [
    "provider_calls_made",
    "local_llm_calls_made",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
]
LEAKS_FOUND_BEFORE_PATCH = {
    "red_run_failure_count": 368,
    "clusters": [
        "RouteSignal-era proactive qualification guidance leaked inbound demo/demo follow-up wording.",
        "Direct price and persisted price fallbacks leaked Starter/Growth/$29/$59 wording.",
        "Previous-question and next-step repairs leaked inbound demo/manual tracking/missed callbacks wording.",
        "Stability and duplicate repairs reused RouteSignal gap-progression text for generic campaigns.",
    ],
}
PATCHES_MADE = [
    "Passed campaign into anti-loop, duplicate-response, and pre-speech stability repair paths.",
    "Added generic-campaign fallback helpers for purpose, next-step, product detail, price, claim-boundary, and focus repair text.",
    "Branched shared RouteSignal-era fallback functions for non-RouteSignal generic campaigns while preserving RouteSignal text.",
    "Expanded generic claim-boundary detection for promise/compliant wording and avoided guardrail-triggering guarantee text in generic fallback repair.",
]
STATIC_AUDIT_FILES = [
    "runtime/core/live_voice_session_policy.py",
    "runtime/core/contextual_buyer_semantics.py",
    "runtime/core/dialogue_pragmatics.py",
    "runtime/core/realtime_turns.py",
    "runtime/entrypoints/generate_guarded_response.py",
    "runtime/entrypoints/generic_campaign_turn.py",
    "scripts/run_live_demo_001_agent_voice_call.py",
    "runtime/voice/runtime_voice_delivery.py",
    "runtime/voice/runtime_tts_delivery.py",
]
SCENARIOS: dict[str, list[str]] = {
    "call_purpose_identity": [
        "__agent_open__",
        "what is this about?",
        "who are you?",
        "why are you calling?",
    ],
    "confusion_previous_question_repair": [
        "__agent_open__",
        "yeah sure",
        "I don't understand",
        "what do you mean?",
        "can you explain that?",
    ],
    "product_offer_detail_question": [
        "__agent_open__",
        "yeah sure",
        "what does this do?",
        "what is included?",
    ],
    "price_cost_question": [
        "__agent_open__",
        "yeah sure",
        "how much does it cost?",
        "is it expensive?",
    ],
    "security_compliance_guarantee_question": [
        "__agent_open__",
        "yeah sure",
        "is this guaranteed?",
        "can you promise that?",
        "is this compliant?",
    ],
    "next_step_question": [
        "__agent_open__",
        "yeah sure",
        "what happens next?",
        "what is the next step?",
    ],
    "low_information_odd_turns": [
        "__agent_open__",
        "yeah sure",
        "okay",
        "maybe",
        "huh",
    ],
    "out_of_scope_irrelevant": [
        "__agent_open__",
        "yeah sure",
        "do you sell cars?",
        "can you help with my password?",
    ],
    "generic_fallback_after_failed_candidate": [
        "__agent_open__",
        "yeah sure",
        "blurple workflow quantum thing",
        "what would your product say about that?",
    ],
}


def write_evidence(result: dict[str, Any], report: str) -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(report, encoding="utf-8")


def normalized(text: str) -> str:
    return str(text or "").lower()


def forbidden_matches(text: str) -> list[str]:
    lowered = normalized(text)
    return [term for term in FORBIDDEN_TERMS if term.lower() in lowered]


def tts_input_text(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("tts_input_text") or (((packet.get("packet") or {}).get("tts_delivery") or {}).get("tts_input_text")) or "")


def provider_rendered_text(packet: dict[str, Any]) -> str:
    voice = ((packet.get("packet") or {}).get("voice_delivery") or {})
    rendering = voice.get("provider_rendering") or {}
    return str(rendering.get("rendered_text") or "")


def selected_action_source(packet: dict[str, Any]) -> str | None:
    manager = packet.get("dialogue_manager") or {}
    selected = manager.get("selected_action") or {}
    return selected.get("source")


def semantic_frame(packet: dict[str, Any]) -> dict[str, Any]:
    manager = packet.get("dialogue_manager") or {}
    return manager.get("contextual_buyer_semantics") or {}


def fallback_source(packet: dict[str, Any]) -> str | None:
    body = packet.get("packet") or {}
    decision = body.get("decision_snapshot") or {}
    validation = body.get("validation") or {}
    tts = body.get("tts_delivery") or {}
    for value in [
        decision.get("fallback_source"),
        decision.get("fallback_reason"),
        validation.get("fallback_reason"),
        tts.get("fallback_reason"),
        (body.get("retrieval") or {}).get("blocked_reason"),
    ]:
        if value:
            return str(value)
    return None


def clean_text_sources(packet: dict[str, Any]) -> dict[str, str]:
    return {
        "final_response": final_response(packet),
        "tts_input_text": tts_input_text(packet),
        "provider_rendered_text": provider_rendered_text(packet),
    }


def assert_no_generic_leakage(failures: list[str], packet: dict[str, Any], label: str) -> None:
    for source, text in clean_text_sources(packet).items():
        found = forbidden_matches(text)
        assert_condition(
            failures,
            not found,
            f"{label}: {source} leaked forbidden generic-campaign terms {found}: {sanitize(text)}",
        )


def assert_safety(failures: list[str], packet: dict[str, Any], label: str) -> None:
    for key in SAFETY_KEYS:
        assert_condition(failures, packet.get(key) is False, f"{label}: {key} must be false: {snapshot(packet)}")
    assert_condition(failures, packet.get("provider_agent_used") is False, f"{label}: provider agent must be false")
    assert_condition(failures, packet.get("durable_provider_agent_created") is False, f"{label}: durable provider agent must be false")
    assert_condition(failures, packet.get("voice_cloning_used") is False, f"{label}: voice cloning must be false")


def assert_generic_playbook(failures: list[str], packet: dict[str, Any], label: str) -> None:
    playbook_id = str(packet.get("campaign_playbook_id") or "")
    assert_condition(
        failures,
        playbook_id and playbook_id != ROUTESIGNAL_PLAYBOOK_ID,
        f"{label}: generic packet used RouteSignal/default playbook: {snapshot(packet)}",
    )
    frame_playbook = str(semantic_frame(packet).get("playbook_id") or "")
    if frame_playbook:
        assert_condition(failures, frame_playbook == playbook_id, f"{label}: semantic playbook mismatch: {snapshot(packet)}")


def is_appointment_pressure(packet: dict[str, Any]) -> bool:
    text = normalized(final_response(packet))
    return any(
        phrase in text
        for phrase in [
            "what time works",
            "quick call",
            "appointment",
            "schedule",
            "book",
            "calendar",
        ]
    )


def run_turn(campaign: dict[str, Any], transcript: str, state: dict[str, Any], session_id: str) -> dict[str, Any]:
    packet = generic_campaign_turn.build_generic_campaign_turn_packet(
        transcript=transcript,
        campaign=campaign,
        input_type="agent-open" if transcript == "__agent_open__" else "speech-final",
        session_id=session_id,
        session_state=state,
        private_out=TMP_DIR / session_id,
        live_tts=False,
        force_key_missing=True,
        timeout_seconds=8.0,
    )
    append_turn(state, packet)
    return packet


def run_sequence(campaign: dict[str, Any], sequence: list[str], session_id: str) -> list[dict[str, Any]]:
    state: dict[str, Any] = {"turns": []}
    packets = []
    for transcript in sequence:
        packets.append(run_turn(campaign, transcript, state, session_id))
    return packets


def static_symbol(lines: list[str], index: int) -> str:
    for cursor in range(index, max(-1, index - 80), -1):
        stripped = lines[cursor].strip()
        if stripped.startswith("def "):
            return stripped.split(":", 1)[0]
        if stripped.startswith("class "):
            return stripped.split(":", 1)[0]
    return "module"


def classify_static_hit(path: str, symbol: str, line_text: str) -> str:
    if path == "scripts/run_live_demo_001_agent_voice_call.py":
        return "allowed_route_signal_only"
    if "validate" in path or "generated" in path:
        return "allowed_generated_evidence_or_validator"
    if path == "runtime/entrypoints/generic_campaign_turn.py" and "ROUTESIGNAL" in line_text:
        return "allowed_route_signal_only"
    route_signal_only_symbols = {
        "live_demo_price_answer(language: str) -> str",
        "is_live_demo_price_answer(response: str) -> bool",
        "is_starter_growth_plan_boundary_question(normalized: str) -> bool",
        "starter_growth_plan_boundary_response(language: str, turns: list[dict] | None = None) -> str",
        "english_guided_option_plan_feature_matrix(campaign: dict | None) -> dict[str, str] | None",
        "is_english_guided_option_selection_turn(transcript: str) -> bool",
    }
    if symbol in route_signal_only_symbols:
        return "allowed_route_signal_only"
    shared_symbols = {
        "opening_text(language: str, campaign: dict | None = None) -> str",
        "identity_repair_text(language: str, campaign: dict | None = None) -> str",
        "call_context_recovery_response(normalized: str, resolved_focus: str | None, language: str, campaign: dict | None = None) -> dict | None",
        "public_crm_boundary_response(normalized: str, campaign: dict | None) -> str",
        "focus_followup_text(language: str, focus: str, normalized: str) -> str",
        "continuity_text(language: str, focus: str, *, persisted: bool = False) -> str",
        "modular_qualification_guidance_text(language: str, step: int) -> str",
        "progressive_focus_text(language: str, focus: str, normalized: str, step: int) -> str",
        "clear_no_pain_response(language: str) -> str",
        "exhausted_progression_options(language: str, focus: str) -> list[str]",
        "compose_candidate_response(",
    }
    if symbol in shared_symbols:
        return "uncertain_needs_runtime_test"
    if path in {
        "runtime/core/live_voice_session_policy.py",
        "runtime/core/contextual_buyer_semantics.py",
        "runtime/core/dialogue_pragmatics.py",
        "runtime/core/realtime_turns.py",
        "runtime/entrypoints/generate_guarded_response.py",
    }:
        return "uncertain_needs_runtime_test"
    return "allowed_route_signal_only"


def static_fallback_surface_audit() -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for relative in STATIC_AUDIT_FILES:
        path = ROOT / relative
        if not path.exists():
            findings.append(
                {
                    "path": relative,
                    "line": None,
                    "symbol": "missing_file",
                    "term": None,
                    "classification": "uncertain_needs_runtime_test",
                    "text": "file missing",
                }
            )
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            found_terms = forbidden_matches(line)
            if not found_terms:
                continue
            symbol = static_symbol(lines, index)
            for term in found_terms:
                findings.append(
                    {
                        "path": relative,
                        "line": index + 1,
                        "symbol": symbol,
                        "term": term,
                        "classification": classify_static_hit(relative, symbol, line),
                        "text": line.strip(),
                    }
                )
    return findings


def validate_dynamic_scenarios(failures: list[str], evidence: dict[str, Any]) -> None:
    campaigns = synthetic_campaigns()
    scenario_rows: list[dict[str, Any]] = []
    for vertical in TARGET_VERTICALS:
        campaign = campaigns[vertical]
        assert_condition(failures, campaign.get("vertical_id") == vertical, f"{vertical}: synthetic campaign mismatch")
        for scenario_id, sequence in SCENARIOS.items():
            packets = run_sequence(
                campaign,
                sequence,
                session_id=f"{CHECKPOINT_ID}-{vertical}-{scenario_id}",
            )
            last_packet = packets[-1]
            for turn_index, packet in enumerate(packets, start=1):
                label = f"{vertical}/{scenario_id}/turn-{turn_index}/{packet.get('transcript')}"
                assert_generic_playbook(failures, packet, label)
                assert_no_generic_leakage(failures, packet, label)
                assert_safety(failures, packet, label)
            if scenario_id == "confusion_previous_question_repair":
                for packet in packets[2:]:
                    assert_condition(
                        failures,
                        not is_appointment_pressure(packet),
                        f"{vertical}/{scenario_id}: confusion turn pressured appointment: {snapshot(packet)}",
                    )
            if scenario_id == "price_cost_question":
                text = normalized(final_response(last_packet))
                assert_condition(
                    failures,
                    "approved" in text or "pricing" in text or "cost" in text or "price" in text or "specialist" in text or "review" in text,
                    f"{vertical}/{scenario_id}: price fallback should stay safe and explicit: {snapshot(last_packet)}",
                )
            if scenario_id == "security_compliance_guarantee_question":
                text = normalized(final_response(last_packet))
                assert_condition(
                    failures,
                    any(token in text for token in ["cannot", "can't", "not claim", "review", "verify", "specialist"]),
                    f"{vertical}/{scenario_id}: guarantee/compliance fallback should avoid unsupported claims: {snapshot(last_packet)}",
                )
            if scenario_id == "next_step_question":
                text = normalized(final_response(last_packet))
                target = normalized(str(campaign.get("appointment_target") or ""))
                owner = normalized(str(campaign.get("human_followup_owner") or ""))
                assert_condition(
                    failures,
                    bool(target and target in text) or bool(owner and owner in text) or "review" in text,
                    f"{vertical}/{scenario_id}: next-step fallback should use campaign follow-up target: {snapshot(last_packet)}",
                )
            responses = [final_response(packet) for packet in packets if final_response(packet)]
            assert_condition(
                failures,
                len(set(responses)) >= min(2, len(responses)),
                f"{vertical}/{scenario_id}: fallback looped the same text excessively: {responses}",
            )
            frame = semantic_frame(last_packet)
            scenario_rows.append(
                sanitize(
                    {
                        "vertical": vertical,
                        "scenario_id": scenario_id,
                        "turn_count": len(packets),
                        "last_transcript": last_packet.get("transcript"),
                        "last_final_response": final_response(last_packet),
                        "last_tts_input_text": tts_input_text(last_packet),
                        "last_provider_rendered_text": provider_rendered_text(last_packet),
                        "last_selected_action_source": selected_action_source(last_packet),
                        "last_semantic": frame.get("semantic"),
                        "last_target_gap": frame.get("target_gap"),
                        "last_fallback_source": fallback_source(last_packet),
                        "call_control": (last_packet.get("summary") or {}).get("call_control"),
                    }
                )
            )
    evidence["dynamic_scenarios"] = scenario_rows


def validate_route_signal_preservation(failures: list[str], evidence: dict[str, Any]) -> None:
    validate_routesignal_preservation(failures, evidence)
    route = evidence.get("routesignal_preservation") or {}
    packets = route if isinstance(route, list) else route.get("packets") or []
    joined = json.dumps(packets)
    evidence["routesignal_terms_allowed_and_present"] = bool(forbidden_matches(joined))


def render_report(result: dict[str, Any]) -> str:
    static_counts: dict[str, int] = {}
    for finding in result.get("static_findings") or []:
        key = str(finding.get("classification"))
        static_counts[key] = static_counts.get(key, 0) + 1
    lines = [
        "# GENERIC-CAMPAIGN-FALLBACK-LEAKAGE-001",
        "",
        f"- Status: `{result['status']}`",
        f"- Failure count: `{result['failure_count']}`",
        f"- Static finding counts: `{json.dumps(static_counts, sort_keys=True)}`",
        f"- Dynamic scenarios covered: `{len(result.get('dynamic_scenarios') or [])}`",
        f"- Leaks found before patch: `{result.get('leaks_found_before_patch', {}).get('red_run_failure_count')}`",
        f"- RouteSignal preservation: `{str(result.get('routesignal_preservation_checked')).lower()}`",
        f"- Provider calls made: `{str(result['safety']['provider_calls_made']).lower()}`",
        f"- Local LLM calls made: `{str(result['safety']['local_llm_calls_made']).lower()}`",
        "",
        "## Static Findings",
        "",
    ]
    for finding in result.get("static_findings") or []:
        lines.append(
            f"- `{finding.get('classification')}` `{finding.get('path')}:{finding.get('line')}` "
            f"`{finding.get('symbol')}` term=`{finding.get('term')}`"
        )
    lines.extend(["", "## Failures", ""])
    if result.get("failures"):
        lines.extend(f"- {failure}" for failure in result["failures"])
    else:
        lines.append("- None")
    lines.extend(["", "## Patches Made", ""])
    lines.extend(f"- {patch}" for patch in result.get("patches_made") or [])
    lines.extend(
        [
            "",
            "## Dynamic Scenarios",
            "",
            "- Covered call purpose/identity, confusion repair, product detail, price, guarantee/compliance, next-step, low-information, out-of-scope, and unknown fallback turns across all eight synthetic verticals.",
            "- Checked final_response, tts_input_text, and provider_rendered_text for forbidden generic-campaign leakage terms.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    failures: list[str] = []
    evidence: dict[str, Any] = {}
    static_findings = static_fallback_surface_audit()
    evidence["static_findings"] = static_findings
    validate_dynamic_scenarios(failures, evidence)
    validate_route_signal_preservation(failures, evidence)

    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "pass" if not failures else "fail",
        "failure_count": len(failures),
        "failures": failures,
        "static_findings": static_findings,
        "dynamic_scenarios": evidence.get("dynamic_scenarios") or [],
        "routesignal_preservation": sanitize(evidence.get("routesignal_preservation") or {}),
        "routesignal_preservation_checked": bool(evidence.get("routesignal_preservation")),
        "routesignal_terms_allowed_and_present": bool(evidence.get("routesignal_terms_allowed_and_present")),
        "forbidden_generic_terms_checked": FORBIDDEN_TERMS,
        "leaks_found_before_patch": LEAKS_FOUND_BEFORE_PATCH,
        "verticals_tested": TARGET_VERTICALS,
        "scenarios_tested": sorted(SCENARIOS),
        "patches_made": PATCHES_MADE,
        "phase_1_2_3_backpatch_required": False,
        "raw_synthetic_emails_in_public_evidence": False,
        "safety": {key: False for key in SAFETY_KEYS},
    }
    serialized = json.dumps(sanitize(result)).lower()
    result["raw_synthetic_emails_in_public_evidence"] = any(raw in serialized for raw in RAW_EMAILS)
    if result["raw_synthetic_emails_in_public_evidence"]:
        result["failures"].append("public generated evidence leaked raw synthetic email")
        result["failure_count"] = len(result["failures"])
        result["status"] = "fail"
    write_evidence(result, render_report(result))
    if failures:
        print(json.dumps({"status": "fail", "failure_count": len(failures), "result_path": str(RESULT_PATH)}, indent=2))
        return 1
    print(json.dumps({"status": "pass", "failure_count": 0, "result_path": str(RESULT_PATH)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
