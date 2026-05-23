"""Validate universal next-step discipline after appointment readiness.

This focused validator covers callback, send-info, concrete timing, vague
timing, and callback-capture garble behavior. It uses dry-run turn builders
only and performs no provider, live TTS, email, calendar, CRM, or PROD-102
actions.
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


CHECKPOINT_ID = "UNIVERSAL-NEXT-STEP-DISCIPLINE-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID
EXAMPLES = ROOT / "runtime" / "campaigns" / "examples"

CAMPAIGNS = [
    {
        "id": "routesignal_live_demo",
        "config_path": None,
        "pain": "callbacks are a problem",
        "expected_gap": "callbacks",
    },
    {
        "id": "synthetic-insurance-review",
        "config_path": EXAMPLES / "synthetic-insurance-review.json",
        "pain": "premium is a problem",
        "expected_gap": "premium_or_budget",
    },
    {
        "id": "synthetic-b2b-saas-operations",
        "config_path": EXAMPLES / "synthetic-b2b-saas-operations.json",
        "pain": "manual work is a problem",
        "expected_gap": "manual_work",
    },
    {
        "id": "synthetic-automotive-service-review",
        "config_path": EXAMPLES / "synthetic-automotive-service-review.json",
        "pain": "repair timings are usually pretty long",
        "expected_gap": "repair_timing",
    },
    {
        "id": "synthetic-home-services-estimate",
        "config_path": EXAMPLES / "synthetic-home-services-estimate.json",
        "pain": "we need service",
        "expected_gap": "service_need",
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

CALLBACK_ASK_PATTERNS = [
    "callback window",
    "time window",
    "what time",
    "what day",
    "which day",
    "preferred window",
    "what works",
]

CONTACT_ASK_PATTERNS = [
    "what email",
    "email should",
    "email or callback",
    "contact",
    "callback path",
    "callback window",
]

FAKE_SIDE_EFFECT_CLAIMS = [
    "i sent",
    "i have sent",
    "i'll send",
    "i will send",
    "calendar invite",
    "booked",
    "scheduled it",
    "crm",
]

WEAK_STOP_DEFAULTS = [
    "if not, i can stop here",
    "we can leave it there",
    "should i stop here",
    "or stop here",
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


def response(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("final_response") or packet.get("final_response") or "")


def lower_response(packet: dict[str, Any]) -> str:
    return response(packet).lower()


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


def asks_callback_window(text: str) -> bool:
    normalized = text.lower()
    return any(pattern in normalized for pattern in CALLBACK_ASK_PATTERNS)


def asks_contact_path(text: str) -> bool:
    normalized = text.lower()
    return any(pattern in normalized for pattern in CONTACT_ASK_PATTERNS)


def has_fake_side_effect_claim(text: str) -> bool:
    normalized = text.lower()
    return any(pattern in normalized for pattern in FAKE_SIDE_EFFECT_CLAIMS)


def has_weak_stop_default(text: str) -> bool:
    normalized = text.lower()
    return any(pattern in normalized for pattern in WEAK_STOP_DEFAULTS)


def question_count(text: str) -> int:
    return text.count("?")


def add_failure(failures: list[str], message: str) -> None:
    if message not in failures:
        failures.append(message)


def common_assertions(packet: dict[str, Any], failures: list[str]) -> None:
    for key, value in side_effect_flags(packet).items():
        if value:
            add_failure(failures, f"side effect flag true: {key}")
    text = lower_response(packet)
    for phrase in ["i should", "approved qualified reviewer path", "approved scope here", "i am asking whether"]:
        if phrase in text:
            add_failure(failures, f"internal wording leaked: {phrase}")
    for phrase in ["we guarantee", "i guarantee", "guaranteed result", "exact price is", "covered for sure"]:
        if phrase in text:
            add_failure(failures, f"unsafe claim leaked: {phrase}")
    if has_fake_side_effect_claim(response(packet)):
        add_failure(failures, "fake email/calendar/CRM action claimed")
    if question_count(response(packet)) > 1:
        add_failure(failures, "more than one question asked")


def expect_universal_next_step(packet: dict[str, Any], failures: list[str], expected_moves: set[str]) -> None:
    current = frame(packet)
    move = str(current.get("buyer_move_id") or "")
    if move not in expected_moves:
        add_failure(failures, f"buyer_move_id expected {sorted(expected_moves)}, got {move}")
    if current.get("response_shape_enforcement_enabled") is not True:
        add_failure(failures, "next-step response-shape enforcement not enabled")
    if current.get("response_shape_enforced_category") != "appointment_callback_send_info":
        add_failure(
            failures,
            f"expected appointment_callback_send_info enforcement, got {current.get('response_shape_enforced_category')}",
        )
    if source(packet) != "universal_response_shape":
        add_failure(failures, f"expected universal_response_shape source, got {source(packet)}")


def expect_gap_preserved(packet: dict[str, Any], campaign: dict[str, Any], failures: list[str]) -> None:
    expected = campaign["expected_gap"]
    current = frame(packet)
    sem = semantic(packet)
    mem = memory(packet)
    confirmed = set(mem.get("confirmed_gaps") or [])
    candidates = {
        str(current.get("confirmed_gap_id") or ""),
        str(current.get("selected_gap") or ""),
        str(sem.get("target_gap") or ""),
        *confirmed,
    }
    if expected not in candidates:
        add_failure(failures, f"confirmed gap not preserved: expected {expected}, got {sorted(candidates)}")


def evaluate_scenario(label: str, campaign: dict[str, Any], packets: list[dict[str, Any]]) -> dict[str, Any]:
    packet = packets[-1]
    failures: list[str] = []
    common_assertions(packet, failures)
    text = response(packet)
    current = frame(packet)
    if has_full_menu(text):
        add_failure(failures, "full diagnostic menu repeated")

    if label == "impact_to_callback_ask":
        if current.get("buyer_move_id") != "implication_confirmed":
            add_failure(failures, f"expected implication_confirmed, got {current.get('buyer_move_id')}")
        if current.get("appointment_readiness") not in {"high", "medium"}:
            add_failure(failures, f"appointment readiness not high/medium: {current.get('appointment_readiness')}")
        if not asks_callback_window(text):
            add_failure(failures, "callback/time-window ask missing after confirmed impact")
        if has_weak_stop_default(text):
            add_failure(failures, "weak stop-offer default used despite readiness")
        if "would a review be useful" in lower_response(packet):
            add_failure(failures, "reopened usefulness question after impact confirmation")
        if call_control(packet) != "continue-call":
            add_failure(failures, f"expected continue-call, got {call_control(packet)}")
    elif label == "send_info_before_readiness":
        expect_universal_next_step(packet, failures, {"send_info_request"})
        if not asks_contact_path(text):
            add_failure(failures, "send-info contact/callback capture missing")
        if call_control(packet) != "continue-call":
            add_failure(failures, f"expected continue-call, got {call_control(packet)}")
    elif label == "send_info_after_readiness":
        expect_universal_next_step(packet, failures, {"send_info_request"})
        expect_gap_preserved(packet, campaign, failures)
        if current.get("appointment_readiness") not in {"high", "medium"}:
            add_failure(failures, f"readiness lost after send-info request: {current.get('appointment_readiness')}")
        if not asks_contact_path(text):
            add_failure(failures, "send-info after readiness did not ask contact/callback path")
        if call_control(packet) != "continue-call":
            add_failure(failures, f"expected continue-call, got {call_control(packet)}")
    elif label == "vague_callback_request":
        expect_universal_next_step(packet, failures, {"callback_request"})
        expect_gap_preserved(packet, campaign, failures)
        if not asks_callback_window(text):
            add_failure(failures, "vague callback did not ask concrete day/time window")
        if call_control(packet) == "schedule-and-end":
            add_failure(failures, "vague callback scheduled and ended")
    elif label == "concrete_callback_time":
        if current.get("buyer_move_id") != "callback_time_provided":
            add_failure(failures, f"expected callback_time_provided, got {current.get('buyer_move_id')}")
        expect_gap_preserved(packet, campaign, failures)
        if call_control(packet) not in {"schedule-and-end", "continue-call"}:
            add_failure(failures, f"unexpected call_control for callback time: {call_control(packet)}")
        if "wrong person" in lower_response(packet) or "not the right person" in lower_response(packet):
            add_failure(failures, "wrong-contact fallback used for callback time")
    elif label == "available_times":
        expect_universal_next_step(packet, failures, {"buyer_requests_available_times"})
        if "live calendar" not in lower_response(packet) and "calendar" not in lower_response(packet):
            add_failure(failures, "available-times response did not state calendar boundary")
        if not asks_callback_window(text) and not asks_contact_path(text):
            add_failure(failures, "available-times response did not ask preferred window/contact path")
        if call_control(packet) != "continue-call":
            add_failure(failures, f"expected continue-call, got {call_control(packet)}")
    elif label == "email_first":
        expect_universal_next_step(packet, failures, {"buyer_wants_email_before_booking"})
        if not asks_contact_path(text):
            add_failure(failures, "email-first response did not ask for email/contact")
        if call_control(packet) != "continue-call":
            add_failure(failures, f"expected continue-call, got {call_control(packet)}")
    elif label == "later_maybe":
        expect_universal_next_step(packet, failures, {"buyer_defers_to_later"})
        if not ("later" in lower_response(packet) or "timing" in lower_response(packet)):
            add_failure(failures, "later response did not acknowledge timing")
        if has_full_menu(text):
            add_failure(failures, "later response repeated full menu")
    elif label == "ambiguous_positive_after_callback_ask":
        expect_universal_next_step(packet, failures, {"appointment_interest"})
        if not asks_callback_window(text):
            add_failure(failures, "ambiguous positive did not ask concrete day/time window")
        if call_control(packet) == "schedule-and-end":
            add_failure(failures, "ambiguous positive scheduled without concrete time")
    elif label == "asr_garble_during_callback_capture":
        current_move = current.get("buyer_move_id")
        if current_move != "asr_garbled_or_low_confidence":
            add_failure(failures, f"expected ASR garble, got {current_move}")
        if current.get("asr_repair_required") is not True:
            add_failure(failures, "ASR repair not required during callback capture")
        if "repeat" not in lower_response(packet) and "caught" not in lower_response(packet) and "misheard" not in lower_response(packet):
            add_failure(failures, "ASR repair response did not ask repeat/rephrase")
        if call_control(packet) == "schedule-and-end":
            add_failure(failures, "garbled callback capture scheduled and ended")
        expect_gap_preserved(packet, campaign, failures)

    return {
        "scenario": label,
        "campaign_id": campaign["id"],
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "buyer_move_id": current.get("buyer_move_id"),
        "response_shape_enforced_category": current.get("response_shape_enforced_category"),
        "appointment_readiness": current.get("appointment_readiness"),
        "sales_progression_stage": current.get("sales_progression_stage"),
        "next_best_sales_action": current.get("next_best_sales_action"),
        "target_gap": (semantic(packet) or {}).get("target_gap"),
        "confirmed_gaps": memory(packet).get("confirmed_gaps"),
        "call_control": call_control(packet),
        "source": source(packet),
        "final_response": response(packet),
        "universal_policy_frame": current,
        "side_effect_flags": side_effect_flags(packet),
    }


def scenario_turns(label: str, campaign: dict[str, Any]) -> list[str]:
    pain_path = ["__agent_open__", "yeah sure", campaign["pain"], "it wastes time"]
    return {
        "impact_to_callback_ask": pain_path,
        "send_info_before_readiness": ["__agent_open__", "send me details"],
        "send_info_after_readiness": [*pain_path, "send me details"],
        "vague_callback_request": [*pain_path, "call me next week"],
        "concrete_callback_time": [*pain_path, "tomorrow at 3 works"],
        "available_times": [*pain_path, "can you send available times"],
        "email_first": [*pain_path, "I need email first"],
        "later_maybe": [*pain_path, "not now maybe later"],
        "ambiguous_positive_after_callback_ask": [*pain_path, "yeah that would be good"],
        "asr_garble_during_callback_capture": [*pain_path, "yadav would be good"],
    }[label]


def write_evidence(results: list[dict[str, Any]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    failures = [result for result in results if result["status"] != "pass"]
    by_scenario: dict[str, dict[str, int]] = defaultdict(lambda: {"passed": 0, "failed": 0})
    failure_types: Counter[str] = Counter()
    side_effects = {key: False for key in SIDE_EFFECT_KEYS}
    for result in results:
        bucket = by_scenario[result["scenario"]]
        bucket["passed" if result["status"] == "pass" else "failed"] += 1
        for failure in result["failures"]:
            failure_types[failure] += 1
        for key, value in (result.get("side_effect_flags") or {}).items():
            side_effects[key] = bool(side_effects.get(key) or value)
    summary = {
        "matrix_size": len(results),
        "pass_count": len(results) - len(failures),
        "failure_count": len(failures),
        "by_scenario": dict(sorted(by_scenario.items())),
        "failure_types": dict(failure_types.most_common()),
        "failure_examples": failures[:10],
    }
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "pass" if not failures else "fail",
        "summary": summary,
        "side_effects": side_effects,
        "results": results,
        "provider_calls_made": False,
        "local_llm_calls_made": False,
        "live_tts_used": False,
        "sends_email": False,
        "creates_calendar_event": False,
        "writes_crm": False,
        "opens_prod_102": False,
        "runtime_behavior_changed": True,
    }
    (OUT_DIR / "result.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    lines = [
        f"# {CHECKPOINT_ID}",
        "",
        f"- Status: `{payload['status']}`",
        f"- Matrix size: `{summary['matrix_size']}`",
        f"- Pass count: `{summary['pass_count']}`",
        f"- Failure count: `{summary['failure_count']}`",
        "",
        "## Scenario Summary",
    ]
    for scenario, counts in sorted(by_scenario.items()):
        lines.append(f"- `{scenario}`: `{counts['passed']}` passed / `{counts['failed']}` failed")
    lines.extend(["", "## Failure Types"])
    if failure_types:
        for failure, count in failure_types.most_common():
            lines.append(f"- `{failure}`: `{count}`")
    else:
        lines.append("- None")
    lines.extend(["", "## Side Effects"])
    for key, value in sorted(side_effects.items()):
        lines.append(f"- `{key}`: `{str(value).lower()}`")
    (OUT_DIR / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    scenarios = [
        "impact_to_callback_ask",
        "send_info_before_readiness",
        "send_info_after_readiness",
        "vague_callback_request",
        "concrete_callback_time",
        "available_times",
        "email_first",
        "later_maybe",
        "ambiguous_positive_after_callback_ask",
        "asr_garble_during_callback_capture",
    ]
    results: list[dict[str, Any]] = []
    for campaign in CAMPAIGNS:
        for scenario in scenarios:
            session_id = f"{CHECKPOINT_ID}-{campaign['id']}-{slug(scenario)}"
            packets = run_sequence(campaign, scenario_turns(scenario, campaign), session_id)
            results.append(evaluate_scenario(scenario, campaign, packets))
    write_evidence(results)
    payload = json.loads((OUT_DIR / "result.json").read_text(encoding="utf-8"))
    print(json.dumps({k: payload[k] for k in ("checkpoint_id", "status", "summary", "side_effects")}, indent=2))
    if payload["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
