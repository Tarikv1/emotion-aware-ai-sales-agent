"""Validate universal pain progression and appointment-readiness behavior.

This checkpoint verifies the commercial progression slice:
permission -> one sharp diagnostic -> pain -> implication check -> readiness
bridge. It uses dry-run turn builders only and performs no provider, live TTS,
email, calendar, CRM, or PROD-102 actions.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import run_live_demo_001_agent_voice_call as demo  # noqa: E402


CHECKPOINT_ID = "UNIVERSAL-PAIN-PROGRESSION-APPOINTMENT-READINESS-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID
EXAMPLES = ROOT / "runtime" / "campaigns" / "examples"

CAMPAIGNS = [
    {
        "id": "routesignal_live_demo",
        "config_path": None,
        "pain_transcript": "callbacks are a problem",
        "pain_gap": "callbacks",
        "tentative_transcript": "maybe handoffs",
        "focus_terms": ["demo follow-up", "follow-up", "callbacks", "handoffs"],
    },
    {
        "id": "synthetic-insurance-review",
        "config_path": EXAMPLES / "synthetic-insurance-review.json",
        "pain_transcript": "premium is a problem",
        "pain_gap": "premium_or_budget",
        "tentative_transcript": "maybe coverage fit",
        "focus_terms": ["premium", "coverage", "budget"],
    },
    {
        "id": "synthetic-b2b-saas-operations",
        "config_path": EXAMPLES / "synthetic-b2b-saas-operations.json",
        "pain_transcript": "manual work is a problem",
        "pain_gap": "manual_work",
        "tentative_transcript": "maybe integration",
        "focus_terms": ["manual work", "integration", "operations"],
    },
    {
        "id": "synthetic-automotive-service-review",
        "config_path": EXAMPLES / "synthetic-automotive-service-review.json",
        "pain_transcript": "repair timings are usually pretty long",
        "pain_gap": "repair_timing",
        "tentative_transcript": "maybe repair timing",
        "focus_terms": ["repair timing", "service advisor", "timing"],
    },
    {
        "id": "synthetic-home-services-estimate",
        "config_path": EXAMPLES / "synthetic-home-services-estimate.json",
        "pain_transcript": "we need service",
        "pain_gap": "service_need",
        "tentative_transcript": "maybe scheduling",
        "focus_terms": ["service need", "scheduling", "service"],
    },
]

FULL_MENU_PATTERNS = [
    "missed callbacks, manual tracking, or handoffs",
    "owner, callback reminder, or handoff",
    "premium or budget, coverage fit, or renewal",
    "premium, coverage fit, or renewal",
    "manual work, integration, or visibility",
    "vehicle issue, repair timing, or warranty",
    "service need, scheduling urgency, or estimate",
    "service need, scheduling, or estimate",
]

APPOINTMENT_ASK_PATTERNS = [
    "what time works",
    "what time should",
    "callback window",
    "time window",
    "note a time",
    "schedule",
    "book",
]

SIDE_EFFECT_KEYS = [
    "provider_calls_made",
    "local_llm_calls_made",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
    "customer_audio_uploaded_to_python_server",
    "customer_audio_uploaded_to_tts_provider",
]


def append_turn(state: dict[str, Any], packet: dict[str, Any]) -> None:
    summary = packet.get("summary") or {}
    state.setdefault("turns", []).append(
        {
            "transcript": packet.get("transcript") or "",
            "summary": summary,
            "continuity": packet.get("demo_session_continuity") or packet.get("conversation_continuity") or {},
            "conversation_memory": packet.get("demo_conversation_memory") or packet.get("conversation_memory") or {},
            "dialogue_manager": packet.get("dialogue_manager") or {},
            "dialogue_pragmatics": packet.get("dialogue_pragmatics") or {},
            "universal_policy_frame": packet.get("universal_policy_frame") or {},
        }
    )
    for key in (
        "conversation_continuity",
        "conversation_memory",
        "dialogue_manager",
        "dialogue_pragmatics",
        "universal_policy_frame",
    ):
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
        campaign_config_path=campaign["config_path"],
        session_id=session_id,
        session_state=state,
        asr_confidence=0.94,
        generic_live_tts_allowed=False,
    )
    append_turn(state, packet)
    return packet


def run_sequence(campaign: dict[str, Any], turns: list[str], session_id: str) -> list[dict[str, Any]]:
    state: dict[str, Any] = {}
    return [build_turn(turn, state, campaign, session_id) for turn in turns]


def slug(text: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in text.lower()).strip("-")


def lower_response(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("final_response") or packet.get("final_response") or "").lower()


def response(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("final_response") or packet.get("final_response") or "")


def frame(packet: dict[str, Any]) -> dict[str, Any]:
    return packet.get("universal_policy_frame") or (packet.get("dialogue_manager") or {}).get("universal_policy_frame") or {}


def memory(packet: dict[str, Any]) -> dict[str, Any]:
    return packet.get("conversation_memory") or packet.get("demo_conversation_memory") or {}


def semantic(packet: dict[str, Any]) -> dict[str, Any]:
    manager = packet.get("dialogue_manager") or {}
    selected = manager.get("selected_action") or {}
    return (
        selected.get("contextual_buyer_semantics")
        or selected.get("semantic_frame")
        or manager.get("contextual_buyer_semantics")
        or {}
    )


def call_control(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("call_control") or (packet.get("packet") or {}).get("call_control") or "")


def source(packet: dict[str, Any]) -> str:
    return str(((packet.get("dialogue_manager") or {}).get("selected_action") or {}).get("source") or "")


def side_effect_flags(packet: dict[str, Any]) -> dict[str, bool]:
    tts = packet.get("tts_delivery") or {}
    return {
        "provider_calls_made": bool(packet.get("provider_calls_made") or tts.get("provider_calls_made")),
        "local_llm_calls_made": bool(packet.get("local_llm_calls_made")),
        "sends_email": bool(packet.get("sends_email")),
        "creates_calendar_event": bool(packet.get("creates_calendar_event")),
        "writes_crm": bool(packet.get("writes_crm")),
        "opens_prod_102": bool(packet.get("opens_prod_102")),
        "customer_audio_uploaded_to_python_server": bool(packet.get("customer_audio_uploaded_to_python_server")),
        "customer_audio_uploaded_to_tts_provider": bool(packet.get("customer_audio_uploaded_to_tts_provider")),
    }


def has_full_menu(text: str) -> bool:
    normalized = text.lower()
    return any(pattern in normalized for pattern in FULL_MENU_PATTERNS)


def has_appointment_ask(text: str) -> bool:
    normalized = text.lower()
    return any(pattern in normalized for pattern in APPOINTMENT_ASK_PATTERNS)


def question_count(text: str) -> int:
    return text.count("?")


def add_failure(failures: list[str], message: str) -> None:
    if message not in failures:
        failures.append(message)


def common_assertions(packet: dict[str, Any], failures: list[str]) -> None:
    flags = side_effect_flags(packet)
    for key, value in flags.items():
        if value:
            add_failure(failures, f"side effect flag true: {key}")
    text = lower_response(packet)
    for phrase in ["i should", "approved qualified reviewer path", "approved scope here", "i am asking whether"]:
        if phrase in text:
            add_failure(failures, f"internal wording leaked: {phrase}")
    for phrase in ["we guarantee", "i guarantee", "guaranteed result", "exact price is", "covered for sure"]:
        if phrase in text:
            add_failure(failures, f"unsafe claim leaked: {phrase}")
    if question_count(response(packet)) > 1:
        add_failure(failures, "more than one question asked")


def expect_progression_frame(
    packet: dict[str, Any],
    failures: list[str],
    *,
    buyer_move_id: str,
    readiness: set[str],
    stage: str | None = None,
) -> None:
    current = frame(packet)
    if current.get("buyer_move_id") != buyer_move_id:
        add_failure(failures, f"buyer_move_id expected {buyer_move_id}, got {current.get('buyer_move_id')}")
    if current.get("response_shape_enforcement_enabled") is not True:
        add_failure(failures, "pain progression enforcement not enabled")
    if source(packet) != "universal_response_shape":
        add_failure(failures, f"expected universal_response_shape source, got {source(packet)}")
    if current.get("appointment_readiness") not in readiness:
        add_failure(failures, f"appointment_readiness expected {sorted(readiness)}, got {current.get('appointment_readiness')}")
    if stage and current.get("sales_progression_stage") != stage:
        add_failure(failures, f"sales_progression_stage expected {stage}, got {current.get('sales_progression_stage')}")
    for field in [
        "pain_development_required",
        "implication_check_required",
        "next_best_sales_action",
        "confirmed_gap_phrase",
        "impact_signal_detected",
        "impact_signal_type",
    ]:
        if field not in current:
            add_failure(failures, f"missing frame field: {field}")


def snapshot(campaign: dict[str, Any], scenario: str, packet: dict[str, Any], failures: list[str]) -> dict[str, Any]:
    sem = semantic(packet)
    return {
        "campaign": campaign["id"],
        "scenario": scenario,
        "transcript": packet.get("transcript"),
        "final_response": response(packet),
        "call_control": call_control(packet),
        "source": source(packet),
        "semantic": sem.get("semantic"),
        "target_gap": sem.get("target_gap"),
        "confirmed_gaps": memory(packet).get("confirmed_gaps") or [],
        "universal_policy_frame": frame(packet),
        "side_effect_flags": side_effect_flags(packet),
        "failures": failures,
        "passed": not failures,
    }


def validate_permission(campaign: dict[str, Any]) -> dict[str, Any]:
    packet = run_sequence(campaign, ["__agent_open__", "yeah sure"], f"{campaign['id']}-permission")[-1]
    failures: list[str] = []
    common_assertions(packet, failures)
    expect_progression_frame(
        packet,
        failures,
        buyer_move_id="permission_acknowledgement",
        readiness={"none"},
        stage="permission_diagnostic",
    )
    if semantic(packet).get("semantic") == "pain_confirmed":
        add_failure(failures, "permission was inferred as pain")
    if has_full_menu(response(packet)):
        add_failure(failures, "full menu after permission")
    if has_appointment_ask(response(packet)):
        add_failure(failures, "appointment ask before pain")
    if call_control(packet) != "continue-call":
        add_failure(failures, f"call_control expected continue-call, got {call_control(packet)}")
    return snapshot(campaign, "permission_acknowledgement", packet, failures)


def validate_clean_pain(campaign: dict[str, Any]) -> dict[str, Any]:
    packet = run_sequence(
        campaign,
        ["__agent_open__", "yeah sure", campaign["pain_transcript"]],
        f"{campaign['id']}-clean-pain",
    )[-1]
    failures: list[str] = []
    common_assertions(packet, failures)
    expect_progression_frame(
        packet,
        failures,
        buyer_move_id="pain_confirmed",
        readiness={"medium"},
        stage="pain_confirmed_needs_implication",
    )
    sem = semantic(packet)
    if sem.get("semantic") != "pain_confirmed":
        add_failure(failures, f"semantic expected pain_confirmed, got {sem.get('semantic')}")
    if sem.get("target_gap") != campaign["pain_gap"]:
        add_failure(failures, f"target_gap expected {campaign['pain_gap']}, got {sem.get('target_gap')}")
    if campaign["pain_gap"] not in (memory(packet).get("confirmed_gaps") or []):
        add_failure(failures, f"confirmed gap missing {campaign['pain_gap']}")
    if has_full_menu(response(packet)):
        add_failure(failures, "full menu after pain")
    if has_appointment_ask(response(packet)):
        add_failure(failures, "appointment ask before implication")
    if not any(token in lower_response(packet) for token in ["causing", "slowing", "delay", "admin", "budget", "follow-up", "real"]):
        add_failure(failures, "missing implication/consequence question")
    return snapshot(campaign, "clean_pain_confirmed", packet, failures)


def validate_tentative_pain(campaign: dict[str, Any]) -> dict[str, Any]:
    packet = run_sequence(
        campaign,
        ["__agent_open__", "yeah sure", campaign["tentative_transcript"]],
        f"{campaign['id']}-tentative-pain",
    )[-1]
    failures: list[str] = []
    common_assertions(packet, failures)
    expect_progression_frame(
        packet,
        failures,
        buyer_move_id="tentative_gap_interest",
        readiness={"low"},
        stage="tentative_pain_needs_clarification",
    )
    if semantic(packet).get("semantic") == "pain_confirmed":
        add_failure(failures, "tentative pain was treated as confirmed pain")
    if call_control(packet) == "transfer-or-escalate":
        add_failure(failures, "tentative pain escalated")
    if has_appointment_ask(response(packet)):
        add_failure(failures, "appointment ask after tentative pain")
    if not any(token in lower_response(packet) for token in ["active", "real", "possible", "later", "actually"]):
        add_failure(failures, "tentative pain did not ask active-vs-possible clarification")
    return snapshot(campaign, "tentative_pain", packet, failures)


def validate_impact_confirmed(campaign: dict[str, Any]) -> dict[str, Any]:
    packet = run_sequence(
        campaign,
        ["__agent_open__", "yeah sure", campaign["pain_transcript"], "it causes delays"],
        f"{campaign['id']}-impact-confirmed",
    )[-1]
    failures: list[str] = []
    common_assertions(packet, failures)
    expect_progression_frame(
        packet,
        failures,
        buyer_move_id="implication_confirmed",
        readiness={"medium", "high"},
        stage="implication_confirmed",
    )
    current = frame(packet)
    if current.get("impact_signal_detected") is not True:
        add_failure(failures, "impact signal not detected")
    if current.get("impact_signal_type") not in {"delay", "time", "cost", "risk", "quality", "follow_up"}:
        add_failure(failures, f"impact type missing or wrong: {current.get('impact_signal_type')}")
    if not has_appointment_ask(response(packet)):
        add_failure(failures, "impact confirmed did not bridge to callback/window")
    if call_control(packet) != "continue-call":
        add_failure(failures, f"call_control expected continue-call, got {call_control(packet)}")
    return snapshot(campaign, "impact_confirmed", packet, failures)


def validate_impact_weak(campaign: dict[str, Any]) -> dict[str, Any]:
    packet = run_sequence(
        campaign,
        ["__agent_open__", "yeah sure", campaign["pain_transcript"], "not really, it is just annoying"],
        f"{campaign['id']}-impact-weak",
    )[-1]
    failures: list[str] = []
    common_assertions(packet, failures)
    expect_progression_frame(
        packet,
        failures,
        buyer_move_id="implication_weak_or_denied",
        readiness={"low"},
        stage="implication_weak_or_denied",
    )
    if has_appointment_ask(response(packet)):
        add_failure(failures, "weak impact got appointment pressure")
    if call_control(packet) == "schedule-and-end":
        add_failure(failures, "weak impact scheduled")
    if not any(token in lower_response(packet) for token in ["minor", "not push", "leave it", "no pressure"]):
        add_failure(failures, "weak impact did not reduce pressure")
    return snapshot(campaign, "impact_weak_or_denied", packet, failures)


def validate_time_after_readiness(campaign: dict[str, Any]) -> dict[str, Any]:
    packet = run_sequence(
        campaign,
        ["__agent_open__", "yeah sure", campaign["pain_transcript"], "it causes delays", "tomorrow at 3 works"],
        f"{campaign['id']}-time-after-readiness",
    )[-1]
    failures: list[str] = []
    common_assertions(packet, failures)
    current = frame(packet)
    sem = semantic(packet)
    if current.get("buyer_move_id") != "callback_time_provided" and sem.get("semantic") not in {
        "callback_time_confirmed",
        "appointment_time_confirmed",
        "callback_time_provided",
    }:
        add_failure(failures, f"appointment time not captured: frame={current.get('buyer_move_id')} semantic={sem.get('semantic')}")
    if call_control(packet) not in {"continue-call", "schedule-and-end"}:
        add_failure(failures, f"unexpected call_control after time: {call_control(packet)}")
    return snapshot(campaign, "appointment_time_after_readiness", packet, failures)


def run_matrix() -> list[dict[str, Any]]:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for campaign in CAMPAIGNS:
        rows.append(validate_permission(campaign))
        rows.append(validate_clean_pain(campaign))
        rows.append(validate_tentative_pain(campaign))
        rows.append(validate_impact_confirmed(campaign))
        rows.append(validate_impact_weak(campaign))
        rows.append(validate_time_after_readiness(campaign))
    return rows


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_scenario: dict[str, dict[str, int]] = defaultdict(lambda: {"passed": 0, "failed": 0})
    failure_types: Counter[str] = Counter()
    for row in rows:
        bucket = by_scenario[row["scenario"]]
        bucket["passed" if row["passed"] else "failed"] += 1
        for failure in row["failures"]:
            failure_types[failure] += 1
    return {
        "matrix_size": len(rows),
        "pass_count": sum(1 for row in rows if row["passed"]),
        "failure_count": sum(1 for row in rows if not row["passed"]),
        "by_scenario": dict(sorted(by_scenario.items())),
        "failure_types": dict(failure_types.most_common()),
        "failure_examples": [row for row in rows if not row["passed"]][:12],
    }


def write_evidence(rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    side_effects = {key: any(row["side_effect_flags"].get(key) for row in rows) for key in SIDE_EFFECT_KEYS}
    status = "pass" if summary["failure_count"] == 0 and not any(side_effects.values()) else "fail"
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": status,
        "summary": summary,
        "side_effects": side_effects,
        "results": rows,
        "generated_audio_required": False,
    }
    (OUT_DIR / "result.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    report = [
        f"# {CHECKPOINT_ID}",
        "",
        "## Summary",
        f"Status: {status}",
        f"Matrix size: {summary['matrix_size']}",
        f"Pass/fail: {summary['pass_count']} / {summary['failure_count']}",
        "",
        "## Results By Scenario",
    ]
    for scenario, counts in summary["by_scenario"].items():
        report.append(f"- {scenario}: pass={counts['passed']} fail={counts['failed']}")
    report.extend(["", "## Top Failures"])
    for failure, count in summary["failure_types"].items():
        report.append(f"- {failure}: {count}")
    report.extend(
        [
            "",
            "## Safety Boundary",
            f"- provider/local LLM/email/calendar/CRM/PROD-102/audio side effects: {side_effects}",
        ]
    )
    (OUT_DIR / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({k: payload[k] for k in ["checkpoint_id", "status", "summary", "side_effects"]}, indent=2, sort_keys=True))


def main() -> int:
    rows = run_matrix()
    summary = summarize(rows)
    write_evidence(rows, summary)
    side_effects = {key: any(row["side_effect_flags"].get(key) for row in rows) for key in SIDE_EFFECT_KEYS}
    return 0 if summary["failure_count"] == 0 and not any(side_effects.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
