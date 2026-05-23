"""Validate campaign wording source cleanup for the universal policy runtime.

The universal runtime owns response-shape behavior. Customer-facing campaign
wording must come from campaign configs or campaign adapter/playbook facts.
"""

from __future__ import annotations

from collections import Counter
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core import campaign_playbook_adapter  # noqa: E402
from scripts import run_live_demo_001_agent_voice_call as demo  # noqa: E402


CHECKPOINT_ID = "UNIVERSALIZATION-DRIFT-CLEANUP-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID
EXAMPLES = ROOT / "runtime" / "campaigns" / "examples"
UNIVERSAL_RUNTIME_PATH = ROOT / "runtime" / "core" / "universal_conversation_policy_runtime.py"

GENERIC_CAMPAIGNS = [
    {
        "id": "synthetic-insurance-review",
        "config_path": EXAMPLES / "synthetic-insurance-review.json",
        "primary_issue": "premium pressure",
        "pain": "premium is a problem",
        "expected_permission_fragment": "premium pressure",
        "expected_pain_fragment": "premium pressure is the issue",
    },
    {
        "id": "synthetic-b2b-saas-operations",
        "config_path": EXAMPLES / "synthetic-b2b-saas-operations.json",
        "primary_issue": "manual work",
        "pain": "manual work is a problem",
        "expected_permission_fragment": "manual work",
        "expected_pain_fragment": "manual work is the issue",
    },
    {
        "id": "synthetic-automotive-service-review",
        "config_path": EXAMPLES / "synthetic-automotive-service-review.json",
        "primary_issue": "repair timing",
        "pain": "repair timings are usually pretty long",
        "expected_permission_fragment": "repair timing",
        "expected_pain_fragment": "repair timing is the issue",
    },
    {
        "id": "synthetic-home-services-estimate",
        "config_path": EXAMPLES / "synthetic-home-services-estimate.json",
        "primary_issue": "service need",
        "pain": "we need service",
        "expected_permission_fragment": "service need",
        "expected_pain_fragment": "service need is the issue",
    },
]

SIDE_EFFECT_KEYS = (
    "provider_calls_made",
    "local_llm_calls_made",
    "live_tts_used",
    "tts_provider_calls_made",
    "audio_file_created",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
    "customer_audio_uploaded_to_python_server",
    "customer_audio_uploaded_to_tts_provider",
)

FORBIDDEN_RUNTIME_NEEDLES = (
    "synthetic-insurance-review",
    "synthetic-b2b-saas-operations",
    "synthetic-automotive-service-review",
    "synthetic-home-services-estimate",
    'vertical == "insurance"',
    'vertical == "b2b_saas"',
    'vertical == "automotive_service"',
    'vertical == "home_services"',
    "inbound demo follow-up slipping",
    "callbacks are the issue",
    "handoffs are the concern",
    "follow-up slipping is the issue",
)

CUSTOMER_WORDING_NEEDLES = (
    "premium pressure",
    "manual work",
    "repair timing",
    "service need",
    "coverage fit",
)

CUSTOMER_FACING_FUNCTIONS = (
    "_human_gap_phrase",
    "_primary_gap_phrase",
    "_sharp_diagnostic_gap_phrase",
    "_campaign_purpose_phrase",
    "_permission_response",
    "_time_pressure_response",
    "_scope_relevance_clarification_response",
    "_pain_implication_response",
    "_tentative_gap_response",
    "render_universal_response_outline",
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def function_source_with_start(source: str, name: str) -> tuple[str, int]:
    match = re.search(rf"^def {re.escape(name)}\(.*?(?=^def |\Z)", source, flags=re.M | re.S)
    if not match:
        return "", 0
    return match.group(0), source[: match.start()].count("\n") + 1


def side_effect_flags(packet: dict[str, Any]) -> dict[str, bool]:
    summary = packet.get("summary") or {}
    tts = packet.get("tts_delivery") or {}
    return {
        "provider_calls_made": bool(packet.get("provider_calls_made") or tts.get("provider_calls_made")),
        "local_llm_calls_made": bool(packet.get("local_llm_calls_made")),
        "live_tts_used": bool(packet.get("live_tts_used") or summary.get("live_tts_used")),
        "tts_provider_calls_made": bool(packet.get("tts_provider_calls_made") or summary.get("tts_provider_calls_made")),
        "audio_file_created": bool(packet.get("audio_file_created") or summary.get("tts_audio_file_created")),
        "sends_email": bool(packet.get("sends_email")),
        "creates_calendar_event": bool(packet.get("creates_calendar_event")),
        "writes_crm": bool(packet.get("writes_crm")),
        "opens_prod_102": bool(packet.get("opens_prod_102")),
        "customer_audio_uploaded_to_python_server": bool(packet.get("customer_audio_uploaded_to_python_server")),
        "customer_audio_uploaded_to_tts_provider": bool(packet.get("customer_audio_uploaded_to_tts_provider")),
    }


def final_response(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("final_response") or packet.get("final_response") or "")


def call_control(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("call_control") or "")


def append_turn(state: dict[str, Any], packet: dict[str, Any]) -> None:
    state.setdefault("turns", []).append(
        {
            "transcript": packet.get("transcript") or "",
            "summary": packet.get("summary") or {},
            "conversation_memory": packet.get("demo_conversation_memory") or packet.get("conversation_memory") or {},
            "dialogue_manager": packet.get("dialogue_manager") or {},
            "universal_policy_frame": packet.get("universal_policy_frame") or {},
        }
    )
    for key in ("conversation_continuity", "conversation_memory", "dialogue_manager", "dialogue_pragmatics", "universal_policy_frame"):
        if key in packet:
            state[key] = packet[key]


def build_turn(transcript: str, state: dict[str, Any], campaign: dict[str, Any], session_id: str) -> dict[str, Any]:
    packet = demo.build_browser_demo_turn_packet(
        transcript=transcript,
        campaign_id=demo.DEFAULT_CAMPAIGN_ID,
        stage=demo.DEFAULT_STAGE,
        input_type="agent-open" if transcript == "__agent_open__" else "speech-final",
        silence_count=0,
        cases_path=demo.DEFAULT_CASES_PATH,
        private_out=TMP_DIR / session_id,
        live_tts=False,
        force_key_missing=True,
        timeout_seconds=8.0,
        campaign_config_path=campaign.get("config_path"),
        session_id=session_id,
        session_state=state,
        asr_confidence=0.94,
        generic_live_tts_allowed=False,
    )
    append_turn(state, packet)
    return packet


def evaluate_sequence(campaign: dict[str, Any], turns: list[str], session_id: str) -> list[dict[str, Any]]:
    state: dict[str, Any] = {}
    return [build_turn(turn, state, campaign, session_id) for turn in turns]


def static_runtime_checks() -> tuple[list[dict[str, Any]], Counter[str]]:
    source = UNIVERSAL_RUNTIME_PATH.read_text(encoding="utf-8")
    failures: list[dict[str, Any]] = []
    failure_types: Counter[str] = Counter()

    for needle in FORBIDDEN_RUNTIME_NEEDLES:
        if needle in source:
            failures.append({"check": "forbidden_runtime_wording_or_branch", "needle": needle})
            failure_types["forbidden_runtime_wording_or_branch"] += 1

    for function_name in CUSTOMER_FACING_FUNCTIONS:
        block, _ = function_source_with_start(source, function_name)
        if not block:
            failures.append({"check": "missing_customer_facing_function", "function": function_name})
            failure_types["missing_customer_facing_function"] += 1
            continue
        for needle in CUSTOMER_WORDING_NEEDLES:
            if needle in block:
                failures.append({"check": "customer_wording_in_universal_runtime", "function": function_name, "needle": needle})
                failure_types["customer_wording_in_universal_runtime"] += 1
    return failures, failure_types


def config_wording_checks() -> tuple[list[dict[str, Any]], Counter[str]]:
    failures: list[dict[str, Any]] = []
    failure_types: Counter[str] = Counter()

    for campaign in GENERIC_CAMPAIGNS:
        config = read_json(campaign["config_path"])
        if not str(config.get("primary_customer_issue_phrase") or "").strip():
            failures.append({"check": "missing_primary_customer_issue_phrase", "campaign_id": campaign["id"]})
            failure_types["missing_primary_customer_issue_phrase"] += 1
        if not str(config.get("short_relevance_question") or "").strip():
            failures.append({"check": "missing_short_relevance_question", "campaign_id": campaign["id"]})
            failure_types["missing_short_relevance_question"] += 1
        for gap_id, gap in (config.get("diagnostic_gaps") or {}).items():
            if not isinstance(gap, dict):
                continue
            for field in ("customer_facing_phrase", "impact_question_phrase", "value_bridge"):
                if not str(gap.get(field) or "").strip():
                    failures.append({"check": f"missing_gap_{field}", "campaign_id": campaign["id"], "gap_id": gap_id})
                    failure_types[f"missing_gap_{field}"] += 1
            if not (str(gap.get("diagnostic_question_phrase") or "").strip() or gap.get("diagnostic_questions")):
                failures.append({"check": "missing_gap_diagnostic_question_fact", "campaign_id": campaign["id"], "gap_id": gap_id})
                failure_types["missing_gap_diagnostic_question_fact"] += 1
    return failures, failure_types


def routesignal_adapter_checks() -> tuple[list[dict[str, Any]], Counter[str], dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    failure_types: Counter[str] = Counter()
    playbook = campaign_playbook_adapter.resolve_campaign_playbook(
        {"campaign_id": "campaign-prod-005-b2b-software", "product_name": "RouteSignal CRM"}
    )
    context = playbook.get("campaign_context") or {}
    for field in ("primary_customer_issue_phrase", "short_relevance_question", "campaign_purpose_phrase", "product_detail_answer"):
        if not str(context.get(field) or "").strip():
            failures.append({"check": f"routesignal_context_missing_{field}"})
            failure_types[f"routesignal_context_missing_{field}"] += 1
    for gap_id in playbook.get("core_diagnostic_gaps") or []:
        gap = (playbook.get("diagnostic_gaps") or {}).get(gap_id) or {}
        for field in ("customer_facing_phrase", "impact_question_phrase", "value_bridge"):
            if not str(gap.get(field) or "").strip():
                failures.append({"check": f"routesignal_gap_missing_{field}", "gap_id": gap_id})
                failure_types[f"routesignal_gap_missing_{field}"] += 1
    return failures, failure_types, playbook


def behavior_checks() -> tuple[list[dict[str, Any]], Counter[str], list[dict[str, Any]]]:
    failures: list[dict[str, Any]] = []
    failure_types: Counter[str] = Counter()
    evidence: list[dict[str, Any]] = []

    routesignal_packets = evaluate_sequence(
        {"id": "routesignal_live_demo", "config_path": None},
        ["__agent_open__", "yeah sure", "callbacks are a problem", "everything is expensive right now", "I just got out of the hospital"],
        "routesignal-drift-cleanup",
    )
    route_permission = final_response(routesignal_packets[1])
    route_pain = final_response(routesignal_packets[2])
    route_financial = final_response(routesignal_packets[3])
    route_hardship = final_response(routesignal_packets[4])
    if "inbound demo follow-up" not in route_permission:
        failures.append({"check": "routesignal_permission_not_preserved", "response": route_permission})
        failure_types["routesignal_permission_not_preserved"] += 1
    if "callbacks are the issue" not in route_pain:
        failures.append({"check": "routesignal_pain_not_preserved", "response": route_pain})
        failure_types["routesignal_pain_not_preserved"] += 1
    if "inbound demo follow-up" not in route_financial:
        failures.append({"check": "routesignal_rapport_bridge_not_using_adapter_issue", "response": route_financial})
        failure_types["routesignal_rapport_bridge_not_using_adapter_issue"] += 1
    if call_control(routesignal_packets[4]) != "end-call":
        failures.append({"check": "serious_hardship_not_terminal", "campaign_id": "routesignal_live_demo", "response": route_hardship})
        failure_types["serious_hardship_not_terminal"] += 1
    evidence.append(
        {
            "campaign_id": "routesignal_live_demo",
            "permission_response": route_permission,
            "pain_response": route_pain,
            "financial_stress_response": route_financial,
            "hardship_response": route_hardship,
            "hardship_call_control": call_control(routesignal_packets[4]),
            "side_effect_flags": side_effect_flags(routesignal_packets[-1]),
        }
    )

    for campaign in GENERIC_CAMPAIGNS:
        packets = evaluate_sequence(
            campaign,
            ["__agent_open__", "yeah sure", campaign["pain"], "everything is expensive right now", "my account number is [REDACTED_ACCOUNT_NUMBER]"],
            f"{campaign['id']}-drift-cleanup",
        )
        permission = final_response(packets[1])
        pain = final_response(packets[2])
        financial = final_response(packets[3])
        sensitive = final_response(packets[4])
        if campaign["expected_permission_fragment"] not in permission:
            failures.append({"check": "generic_permission_not_preserved", "campaign_id": campaign["id"], "response": permission})
            failure_types["generic_permission_not_preserved"] += 1
        if campaign["expected_pain_fragment"] not in pain:
            failures.append({"check": "generic_pain_not_preserved", "campaign_id": campaign["id"], "response": pain})
            failure_types["generic_pain_not_preserved"] += 1
        if campaign["primary_issue"] not in financial:
            failures.append({"check": "generic_rapport_bridge_not_using_config_issue", "campaign_id": campaign["id"], "response": financial})
            failure_types["generic_rapport_bridge_not_using_config_issue"] += 1
        if call_control(packets[4]) != "end-call":
            failures.append({"check": "sensitive_data_not_terminal", "campaign_id": campaign["id"], "response": sensitive})
            failure_types["sensitive_data_not_terminal"] += 1
        evidence.append(
            {
                "campaign_id": campaign["id"],
                "permission_response": permission,
                "pain_response": pain,
                "financial_stress_response": financial,
                "sensitive_data_response": sensitive,
                "sensitive_call_control": call_control(packets[4]),
                "side_effect_flags": side_effect_flags(packets[-1]),
            }
        )
    return failures, failure_types, evidence


def review_packet_drift_summary() -> dict[str, Any]:
    packet_path = ROOT / "research" / "experiments" / "generated" / "COMMERCIAL-SALES-CONVERSATION-REVIEW-001" / "review_packet.json"
    if not packet_path.exists():
        return {"checked": False, "reason": "commercial_review_packet_not_found"}
    packet = read_json(packet_path)
    findings = packet.get("universalization_drift_findings") or []
    active = [item for item in findings if item.get("id") in {"UDR-001", "UDR-002", "UDR-003", "UDR-004"}]
    return {
        "checked": True,
        "active_udr_findings": active,
        "all_findings": findings,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    static_failures, static_types = static_runtime_checks()
    config_failures, config_types = config_wording_checks()
    adapter_failures, adapter_types, routesignal_playbook = routesignal_adapter_checks()
    behavior_failures, behavior_types, behavior_evidence = behavior_checks()
    drift_summary = review_packet_drift_summary()

    failures = static_failures + config_failures + adapter_failures + behavior_failures
    failure_types = static_types + config_types + adapter_types + behavior_types
    if drift_summary.get("checked") and drift_summary.get("active_udr_findings"):
        failures.append({"check": "active_review_packet_udr_findings", "findings": drift_summary["active_udr_findings"]})
        failure_types["active_review_packet_udr_findings"] += 1

    side_effects = {key: False for key in SIDE_EFFECT_KEYS}
    for item in behavior_evidence:
        for key, value in (item.get("side_effect_flags") or {}).items():
            side_effects[key] = bool(side_effects.get(key) or value)
    for key, value in side_effects.items():
        if value:
            failures.append({"check": "side_effect_flag_true", "flag": key})
            failure_types["side_effect_flag_true"] += 1

    summary = {
        "status": "pass" if not failures else "fail",
        "failure_count": len(failures),
        "failure_types": dict(sorted(failure_types.items())),
        "failure_examples": failures[:20],
        "static_checks": {
            "synthetic_campaign_id_branches_removed": not any(item.get("needle", "").startswith("synthetic-") for item in static_failures),
            "vertical_to_phrase_branches_removed": not any("vertical ==" in item.get("needle", "") for item in static_failures),
            "routesignal_wording_in_adapter_not_runtime": not any("inbound demo follow-up" in item.get("needle", "") for item in static_failures),
            "customer_gap_wording_in_config_not_runtime": not any(item.get("check") == "customer_wording_in_universal_runtime" for item in static_failures),
        },
        "wording_source_fields": {
            "campaign_level": ["primary_customer_issue_phrase", "short_relevance_question"],
            "gap_level": ["customer_facing_phrase", "impact_question_phrase", "pain_acknowledgement_phrase"],
            "routesignal_adapter_context_fields": sorted((routesignal_playbook.get("campaign_context") or {}).keys()),
        },
        "behavior_evidence": behavior_evidence,
        "review_packet_drift_summary": drift_summary,
        "side_effects": side_effects,
    }
    payload = {"checkpoint_id": CHECKPOINT_ID, "status": summary["status"], "summary": summary}
    write_json(OUT_DIR / "result.json", payload)

    report = [
        f"# {CHECKPOINT_ID}",
        "",
        "## Summary",
        f"- Status: `{payload['status']}`",
        f"- Failure count: `{summary['failure_count']}`",
        "",
        "## Wording Source Cleanup",
        f"- Synthetic campaign ID branches removed: `{str(summary['static_checks']['synthetic_campaign_id_branches_removed']).lower()}`",
        f"- Vertical-to-primary-phrase branches removed: `{str(summary['static_checks']['vertical_to_phrase_branches_removed']).lower()}`",
        f"- RouteSignal wording sourced from adapter/playbook facts: `{str(summary['static_checks']['routesignal_wording_in_adapter_not_runtime']).lower()}`",
        f"- Generic gap wording sourced from config facts: `{str(summary['static_checks']['customer_gap_wording_in_config_not_runtime']).lower()}`",
        "",
        "## Failure Types",
    ]
    if summary["failure_types"]:
        report.extend(f"- `{key}`: `{value}`" for key, value in summary["failure_types"].items())
    else:
        report.append("- None")
    report.extend(["", "## Behavior Preservation Examples"])
    for item in behavior_evidence:
        report.append(f"- `{item['campaign_id']}` permission: {item['permission_response']}")
        report.append(f"  - Pain: {item['pain_response']}")
        if item.get("financial_stress_response"):
            report.append(f"  - Financial stress bridge: {item['financial_stress_response']}")
        if item.get("hardship_response"):
            report.append(f"  - Serious hardship: {item['hardship_response']} (`{item.get('hardship_call_control')}`)")
        if item.get("sensitive_data_response"):
            report.append(f"  - Sensitive data: {item['sensitive_data_response']} (`{item.get('sensitive_call_control')}`)")
    report.extend(["", "## Review Packet Drift Findings"])
    if drift_summary.get("checked"):
        active = drift_summary.get("active_udr_findings") or []
        if active:
            for item in active:
                report.append(f"- `{item.get('id')}` remains: {item.get('title')}")
        else:
            report.append("- UDR-001 through UDR-004 are absent from the current commercial review packet.")
    else:
        report.append(f"- Not checked: {drift_summary.get('reason')}")
    report.extend(
        [
            "",
            "## Side Effects",
            "- Provider calls, local LLM calls, live TTS, email, calendar, CRM, PROD-102, and customer audio uploads remained false.",
        ]
    )
    (OUT_DIR / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "checkpoint_id": CHECKPOINT_ID,
                "status": payload["status"],
                "failure_count": summary["failure_count"],
                "failure_types": summary["failure_types"],
                "output_dir": str(OUT_DIR),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
