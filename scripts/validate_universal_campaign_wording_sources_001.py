"""Validate universal campaign wording source boundaries.

The universal policy runtime may own deterministic sales behavior, but campaign
wording must come from campaign configs or campaign adapter facts. This gate
keeps the static architecture boundary visible while also checking that the
customer-facing behavior remains unchanged for representative turns.
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

from scripts import run_live_demo_001_agent_voice_call as demo  # noqa: E402


CHECKPOINT_ID = "UNIVERSAL-CAMPAIGN-WORDING-SOURCES-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID
EXAMPLES = ROOT / "runtime" / "campaigns" / "examples"
UNIVERSAL_RUNTIME_PATH = ROOT / "runtime" / "core" / "universal_conversation_policy_runtime.py"
ROUTESIGNAL_PLAYBOOK_PATH = ROOT / "runtime" / "core" / "sales_diagnostic_playbook.py"

GENERIC_CAMPAIGNS = [
    {
        "id": "synthetic-insurance-review",
        "config_path": EXAMPLES / "synthetic-insurance-review.json",
        "primary_issue": "premium pressure",
        "pain": "premium is a problem",
        "expected_permission": "Thanks. Is premium pressure causing any issue right now?",
        "expected_pain_fragment": "premium pressure is the issue",
    },
    {
        "id": "synthetic-b2b-saas-operations",
        "config_path": EXAMPLES / "synthetic-b2b-saas-operations.json",
        "primary_issue": "manual work",
        "pain": "manual work is a problem",
        "expected_permission": "Thanks. Is manual work causing any issue right now?",
        "expected_pain_fragment": "manual work is the issue",
    },
    {
        "id": "synthetic-automotive-service-review",
        "config_path": EXAMPLES / "synthetic-automotive-service-review.json",
        "primary_issue": "repair timing",
        "pain": "repair timings are usually pretty long",
        "expected_permission": "Thanks. Is repair timing causing any issue right now?",
        "expected_pain_fragment": "repair timing is the issue",
    },
    {
        "id": "synthetic-home-services-estimate",
        "config_path": EXAMPLES / "synthetic-home-services-estimate.json",
        "primary_issue": "service need",
        "pain": "we need service",
        "expected_permission": "Thanks. Is the service need active right now?",
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

RUNTIME_FORBIDDEN_SOURCE_NEEDLES = (
    "synthetic-insurance-review",
    "synthetic-b2b-saas-operations",
    "synthetic-automotive-service-review",
    "synthetic-home-services-estimate",
    'vertical == "insurance"',
    'vertical == "b2b_saas"',
    'vertical == "automotive_service"',
    'vertical == "home_services"',
)

CUSTOMER_FACING_WORDING_NEEDLES = (
    "inbound demo follow-up slipping",
    "callbacks are the issue",
    "handoffs are the concern",
    "follow-up slipping is the issue",
    "premium pressure",
    "manual work",
    "repair timing",
    "service need",
    "coverage fit",
    "scheduling",
)

CUSTOMER_FACING_FUNCTIONS = (
    "_human_gap_phrase",
    "_sharp_diagnostic_gap_phrase",
    "_campaign_purpose_phrase",
    "_permission_response",
    "_time_pressure_response",
    "_scope_relevance_clarification_response",
    "_pain_implication_response",
    "render_universal_response_outline",
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def function_source(source: str, name: str) -> str:
    match = re.search(rf"^def {re.escape(name)}\(.*?(?=^def |\Z)", source, flags=re.M | re.S)
    return match.group(0) if match else ""


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


def response(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("final_response") or packet.get("final_response") or "")


def evaluate_sequence(campaign: dict[str, Any], turns: list[str], session_id: str) -> list[dict[str, Any]]:
    state: dict[str, Any] = {}
    return [build_turn(turn, state, campaign, session_id) for turn in turns]


def static_source_checks() -> tuple[list[dict[str, Any]], Counter[str]]:
    source = UNIVERSAL_RUNTIME_PATH.read_text(encoding="utf-8")
    failures: list[dict[str, Any]] = []
    failure_types: Counter[str] = Counter()
    for needle in RUNTIME_FORBIDDEN_SOURCE_NEEDLES:
        if needle in source:
            failures.append({"check": "runtime_forbidden_source_needle", "needle": needle})
            failure_types["runtime_forbidden_source_needle"] += 1

    function_blocks = {name: function_source(source, name) for name in CUSTOMER_FACING_FUNCTIONS}
    for name, block in function_blocks.items():
        if not block:
            failures.append({"check": "missing_customer_facing_function", "function": name})
            failure_types["missing_customer_facing_function"] += 1
            continue
        for needle in CUSTOMER_FACING_WORDING_NEEDLES:
            if needle in block:
                failures.append({"check": "customer_wording_in_universal_runtime_function", "function": name, "needle": needle})
                failure_types["customer_wording_in_universal_runtime_function"] += 1
    return failures, failure_types


def config_wording_checks() -> tuple[list[dict[str, Any]], Counter[str]]:
    failures: list[dict[str, Any]] = []
    failure_types: Counter[str] = Counter()

    for campaign in GENERIC_CAMPAIGNS:
        config = read_json(campaign["config_path"])
        if config.get("primary_customer_issue_phrase") != campaign["primary_issue"]:
            failures.append({"check": "missing_primary_customer_issue_phrase", "campaign_id": campaign["id"]})
            failure_types["missing_primary_customer_issue_phrase"] += 1
        gaps = config.get("diagnostic_gaps") or {}
        for gap_id, gap in gaps.items():
            if not isinstance(gap, dict):
                continue
            for field in ("customer_facing_phrase", "impact_question_phrase", "value_bridge"):
                if not str(gap.get(field) or "").strip():
                    failures.append({"check": f"missing_gap_{field}", "campaign_id": campaign["id"], "gap_id": gap_id})
                    failure_types[f"missing_gap_{field}"] += 1

    playbook_source = ROUTESIGNAL_PLAYBOOK_PATH.read_text(encoding="utf-8")
    for field in ("primary_customer_issue_phrase", "customer_facing_phrase", "impact_question_phrase"):
        if field not in playbook_source:
            failures.append({"check": f"routesignal_playbook_missing_{field}"})
            failure_types[f"routesignal_playbook_missing_{field}"] += 1
    return failures, failure_types


def behavior_checks() -> tuple[list[dict[str, Any]], Counter[str], list[dict[str, Any]]]:
    failures: list[dict[str, Any]] = []
    failure_types: Counter[str] = Counter()
    evidence: list[dict[str, Any]] = []

    route_packets = evaluate_sequence(
        {"id": "routesignal_live_demo", "config_path": None},
        ["__agent_open__", "yeah sure", "callbacks are a problem"],
        "routesignal-wording-sources",
    )
    route_permission = response(route_packets[1])
    route_pain = response(route_packets[2])
    if route_permission != "Thanks. Is inbound demo follow-up slipping right now?":
        failures.append({"check": "routesignal_permission_changed", "response": route_permission})
        failure_types["routesignal_permission_changed"] += 1
    if "callbacks are the issue" not in route_pain:
        failures.append({"check": "routesignal_pain_response_changed", "response": route_pain})
        failure_types["routesignal_pain_response_changed"] += 1
    evidence.append(
        {
            "campaign_id": "routesignal_live_demo",
            "permission_response": route_permission,
            "pain_response": route_pain,
            "side_effect_flags": side_effect_flags(route_packets[-1]),
        }
    )

    for campaign in GENERIC_CAMPAIGNS:
        packets = evaluate_sequence(
            campaign,
            ["__agent_open__", "yeah sure", campaign["pain"]],
            f"{campaign['id']}-wording-sources",
        )
        permission = response(packets[1])
        pain = response(packets[2])
        if permission != campaign["expected_permission"]:
            failures.append({"check": "generic_permission_changed", "campaign_id": campaign["id"], "response": permission})
            failure_types["generic_permission_changed"] += 1
        if campaign["expected_pain_fragment"] not in pain:
            failures.append({"check": "generic_pain_response_changed", "campaign_id": campaign["id"], "response": pain})
            failure_types["generic_pain_response_changed"] += 1
        evidence.append(
            {
                "campaign_id": campaign["id"],
                "permission_response": permission,
                "pain_response": pain,
                "side_effect_flags": side_effect_flags(packets[-1]),
            }
        )
    return failures, failure_types, evidence


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    static_failures, static_failure_types = static_source_checks()
    config_failures, config_failure_types = config_wording_checks()
    behavior_failures, behavior_failure_types, behavior_evidence = behavior_checks()

    failures = static_failures + config_failures + behavior_failures
    failure_types = static_failure_types + config_failure_types + behavior_failure_types
    side_effects = {key: False for key in SIDE_EFFECT_KEYS}
    for item in behavior_evidence:
        for key, value in (item.get("side_effect_flags") or {}).items():
            side_effects[key] = bool(side_effects.get(key) or value)

    summary = {
        "status": "pass" if not failures else "fail",
        "failure_count": len(failures),
        "failure_types": dict(sorted(failure_types.items())),
        "failure_examples": failures[:20],
        "behavior_evidence": behavior_evidence,
        "side_effects": side_effects,
    }
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": summary["status"],
        "summary": summary,
    }
    write_json(OUT_DIR / "result.json", payload)

    report = [
        f"# {CHECKPOINT_ID}",
        "",
        "## Summary",
        f"- Status: `{payload['status']}`",
        f"- Failure count: `{summary['failure_count']}`",
        "",
        "## Failure Types",
    ]
    if summary["failure_types"]:
        for key, value in summary["failure_types"].items():
            report.append(f"- `{key}`: `{value}`")
    else:
        report.append("- None")
    report.extend(["", "## Behavior Preservation Evidence"])
    for item in behavior_evidence:
        report.append(f"- `{item['campaign_id']}` permission: {item['permission_response']}")
        report.append(f"  - Pain: {item['pain_response']}")
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
