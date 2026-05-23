"""Validate tentative pain continuity and repeated ASR repair persistence.

This focused validator covers the commercial gap exposed by the 4E2I review
packet: tentative pain must stay attached to the selected gap after the buyer
confirms it is active, and repeated ASR garble must remain in ASR repair mode.
It uses dry-run turn builders only.
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


CHECKPOINT_ID = "UNIVERSAL-TENTATIVE-PAIN-CONTINUITY-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID
EXAMPLES = ROOT / "runtime" / "campaigns" / "examples"

CAMPAIGNS = [
    {
        "id": "routesignal_live_demo",
        "config_path": None,
        "tentative": "maybe handoffs",
        "pain": "callbacks are a problem",
        "expected_gap": "handoffs",
    },
    {
        "id": "synthetic-insurance-review",
        "config_path": EXAMPLES / "synthetic-insurance-review.json",
        "tentative": "maybe coverage fit",
        "pain": "premium is a problem",
        "expected_gap": "coverage_fit",
    },
    {
        "id": "synthetic-b2b-saas-operations",
        "config_path": EXAMPLES / "synthetic-b2b-saas-operations.json",
        "tentative": "maybe integration",
        "pain": "manual work is a problem",
        "expected_gap": "integration_risk",
    },
    {
        "id": "synthetic-automotive-service-review",
        "config_path": EXAMPLES / "synthetic-automotive-service-review.json",
        "tentative": "maybe repair timing",
        "pain": "repair timings are usually pretty long",
        "expected_gap": "repair_timing",
    },
    {
        "id": "synthetic-home-services-estimate",
        "config_path": EXAMPLES / "synthetic-home-services-estimate.json",
        "tentative": "maybe scheduling",
        "pain": "we need service",
        "expected_gap": "scheduling_urgency",
    },
]

FULL_MENU_PATTERNS = [
    "missed callbacks, manual tracking, or handoffs",
    "premium or budget, coverage fit, or renewal",
    "manual work, integration, or visibility",
    "vehicle issue, repair timing, or warranty",
    "service need, scheduling urgency, or estimate",
    "service need, scheduling, or estimate",
]

STOP_OFFER_PATTERNS = [
    "if not, i can stop here",
    "or stop here",
    "leave it there",
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


def append_state(state: dict[str, Any], packet: dict[str, Any]) -> None:
    state.setdefault("turns", []).append(
        {
            "transcript": packet.get("transcript") or "",
            "summary": packet.get("summary") or {},
            "continuity": packet.get("conversation_continuity") or packet.get("demo_session_continuity") or {},
            "conversation_memory": packet.get("conversation_memory") or packet.get("demo_conversation_memory") or {},
            "dialogue_manager": packet.get("dialogue_manager") or {},
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
    append_state(state, packet)
    return packet


def run_sequence(campaign: dict[str, Any], turns: list[str], session_id: str) -> list[dict[str, Any]]:
    state: dict[str, Any] = {}
    return [build_turn(turn, state, campaign, session_id) for turn in turns]


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


def source(packet: dict[str, Any]) -> str:
    return str(((packet.get("dialogue_manager") or {}).get("selected_action") or {}).get("source") or "")


def call_control(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("call_control") or "")


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


def has_stop_offer_default(text: str) -> bool:
    normalized = text.lower()
    return any(pattern in normalized for pattern in STOP_OFFER_PATTERNS)


def has_callback_ask(text: str) -> bool:
    normalized = text.lower()
    return any(
        pattern in normalized
        for pattern in ["callback window", "what time", "time window", "what callback", "note for the callback"]
    )


def add_failure(failures: list[str], message: str) -> None:
    if message not in failures:
        failures.append(message)


def common_assertions(packet: dict[str, Any], failures: list[str]) -> None:
    for key, value in side_effect_flags(packet).items():
        if value:
            add_failure(failures, f"side effect flag true: {key}")
    text = lower_response(packet)
    for phrase in ["i should", "approved qualified reviewer path", "approved scope here", "internal policy"]:
        if phrase in text:
            add_failure(failures, f"internal wording leaked: {phrase}")


def assert_gap_preserved(packet: dict[str, Any], expected_gap: str, failures: list[str]) -> None:
    sem = semantic(packet)
    mem = memory(packet)
    current_frame = frame(packet)
    confirmed = list(mem.get("confirmed_gaps") or [])
    frame_gap = current_frame.get("confirmed_gap_id") or current_frame.get("selected_gap")
    target_gap = frame_gap or sem.get("target_gap") or current_frame.get("target_gap")
    if expected_gap not in confirmed:
        add_failure(failures, f"confirmed_gaps missing tentative gap {expected_gap}: {confirmed}")
    if target_gap not in {None, expected_gap}:
        add_failure(failures, f"target_gap expected {expected_gap}, got {target_gap}")
    if frame_gap not in {None, "", expected_gap}:
        add_failure(failures, f"frame gap expected {expected_gap}, got {frame_gap}")


def validate_active_confirmation(campaign: dict[str, Any]) -> dict[str, Any]:
    packets = run_sequence(
        campaign,
        ["__agent_open__", "yeah sure", campaign["tentative"], "it is active now"],
        f"{campaign['id']}-active-confirmation",
    )
    packet = packets[-1]
    failures: list[str] = []
    current_frame = frame(packet)
    common_assertions(packet, failures)
    if current_frame.get("buyer_move_id") not in {"pain_confirmed", "active_tentative_gap_confirmed"}:
        add_failure(failures, f"expected active tentative pain confirmation, got {current_frame.get('buyer_move_id')}")
    if current_frame.get("sales_progression_stage") != "pain_confirmed_needs_implication":
        add_failure(failures, f"expected pain_confirmed_needs_implication, got {current_frame.get('sales_progression_stage')}")
    if current_frame.get("implication_check_required") is not True:
        add_failure(failures, "implication_check_required not true")
    assert_gap_preserved(packet, campaign["expected_gap"], failures)
    text = response(packet)
    if "?" not in text:
        add_failure(failures, "response did not ask implication question")
    if has_full_menu(text):
        add_failure(failures, "response repeated full menu")
    if has_stop_offer_default(text):
        add_failure(failures, "response used stop-offer default")
    if source(packet) == "pre_speech_conversation_stability_guard":
        add_failure(failures, "stability guard took over tentative confirmation")
    if call_control(packet) != "continue-call":
        add_failure(failures, f"call_control expected continue-call, got {call_control(packet)}")
    return scenario_result(campaign, "tentative_active_confirmation", packets, failures)


def validate_impact_confirmation(campaign: dict[str, Any]) -> dict[str, Any]:
    packets = run_sequence(
        campaign,
        ["__agent_open__", "yeah sure", campaign["tentative"], "it is active now", "it wastes time"],
        f"{campaign['id']}-impact-confirmation",
    )
    packet = packets[-1]
    failures: list[str] = []
    current_frame = frame(packet)
    common_assertions(packet, failures)
    if current_frame.get("buyer_move_id") != "implication_confirmed":
        add_failure(failures, f"buyer_move_id expected implication_confirmed, got {current_frame.get('buyer_move_id')}")
    if current_frame.get("appointment_readiness") not in {"high", "medium"}:
        add_failure(failures, f"appointment_readiness expected high/medium, got {current_frame.get('appointment_readiness')}")
    if current_frame.get("impact_signal_detected") is not True:
        add_failure(failures, "impact_signal_detected not true")
    assert_gap_preserved(packet, campaign["expected_gap"], failures)
    text = response(packet)
    if not has_callback_ask(text):
        add_failure(failures, "response did not ask callback/time after confirmed impact")
    if has_full_menu(text):
        add_failure(failures, "response repeated full menu")
    if has_stop_offer_default(text):
        add_failure(failures, "response used stop-offer default")
    if call_control(packet) != "continue-call":
        add_failure(failures, f"call_control expected continue-call, got {call_control(packet)}")
    return scenario_result(campaign, "tentative_impact_confirmation", packets, failures)


def validate_appointment_time(campaign: dict[str, Any]) -> dict[str, Any]:
    packets = run_sequence(
        campaign,
        [
            "__agent_open__",
            "yeah sure",
            campaign["tentative"],
            "it is active now",
            "it wastes time",
            "tomorrow at 3 works",
        ],
        f"{campaign['id']}-appointment-time",
    )
    packet = packets[-1]
    failures: list[str] = []
    current_frame = frame(packet)
    sem = semantic(packet)
    common_assertions(packet, failures)
    if current_frame.get("buyer_move_id") != "callback_time_provided":
        add_failure(failures, f"buyer_move_id expected callback_time_provided, got {current_frame.get('buyer_move_id')}")
    if sem.get("semantic") not in {
        "callback_time_provided",
        "appointment_time_confirmed",
        "callback_time_confirmation",
        "appointment_time_given",
    }:
        add_failure(failures, f"semantic expected callback/appointment time, got {sem.get('semantic')}")
    assert_gap_preserved(packet, campaign["expected_gap"], failures)
    if call_control(packet) not in {"schedule-and-end", "continue-call"}:
        add_failure(failures, f"unexpected call_control {call_control(packet)}")
    text = lower_response(packet)
    if "would a review be useful" in text or "what do you mean" in text or "right contact" in text:
        add_failure(failures, "appointment time produced wrong follow-up fallback")
    return scenario_result(campaign, "tentative_appointment_time", packets, failures)


def validate_weak_impact(campaign: dict[str, Any]) -> dict[str, Any]:
    packets = run_sequence(
        campaign,
        [
            "__agent_open__",
            "yeah sure",
            campaign["tentative"],
            "it is active now",
            "not really, just annoying",
        ],
        f"{campaign['id']}-weak-impact",
    )
    packet = packets[-1]
    failures: list[str] = []
    current_frame = frame(packet)
    common_assertions(packet, failures)
    if current_frame.get("buyer_move_id") != "implication_weak_or_denied":
        add_failure(failures, f"buyer_move_id expected implication_weak_or_denied, got {current_frame.get('buyer_move_id')}")
    if current_frame.get("appointment_readiness") != "low":
        add_failure(failures, f"appointment_readiness expected low, got {current_frame.get('appointment_readiness')}")
    assert_gap_preserved(packet, campaign["expected_gap"], failures)
    text = response(packet)
    if has_callback_ask(text):
        add_failure(failures, "weak impact still asked for callback")
    if has_full_menu(text):
        add_failure(failures, "weak impact repeated full menu")
    return scenario_result(campaign, "tentative_weak_impact", packets, failures)


def validate_repeated_asr_garble(campaign: dict[str, Any]) -> dict[str, Any]:
    packets = run_sequence(
        campaign,
        ["__agent_open__", "yeah sure", "play a double be good", "yadav would be good", campaign["pain"]],
        f"{campaign['id']}-repeated-asr",
    )
    failures: list[str] = []
    first_garble = packets[2]
    second_garble = packets[3]
    clean_recovery = packets[4]
    for label, packet in [("first", first_garble), ("second", second_garble)]:
        current_frame = frame(packet)
        common_assertions(packet, failures)
        if current_frame.get("buyer_move_id") != "asr_garbled_or_low_confidence":
            add_failure(failures, f"{label} garble buyer_move_id wrong: {current_frame.get('buyer_move_id')}")
        text = lower_response(packet)
        if "repeat" not in text and "rephrase" not in text:
            add_failure(failures, f"{label} garble did not ask repeat/rephrase")
        if "already answered" in text or "concrete follow-up" in text:
            add_failure(failures, f"{label} garble triggered duplicate-answer repair")
        if source(packet) == "pre_speech_conversation_stability_guard":
            add_failure(failures, f"{label} garble stability guard took over")
    recovery_frame = frame(clean_recovery)
    if recovery_frame.get("buyer_move_id") not in {"pain_confirmed", "implication_confirmed"}:
        add_failure(failures, f"clean recovery did not return to pain path: {recovery_frame.get('buyer_move_id')}")
    if has_full_menu(response(clean_recovery)):
        add_failure(failures, "clean recovery repeated full menu")
    return scenario_result(campaign, "repeated_asr_garble", packets, failures)


def scenario_result(
    campaign: dict[str, Any],
    scenario: str,
    packets: list[dict[str, Any]],
    failures: list[str],
) -> dict[str, Any]:
    last = packets[-1]
    return {
        "campaign": campaign["id"],
        "scenario": scenario,
        "passed": not failures,
        "failures": failures,
        "final_response": response(last),
        "call_control": call_control(last),
        "semantic": semantic(last).get("semantic"),
        "target_gap": semantic(last).get("target_gap"),
        "confirmed_gaps": memory(last).get("confirmed_gaps"),
        "source": source(last),
        "universal_policy_frame": frame(last),
        "turns": [
            {
                "transcript": packet.get("transcript"),
                "final_response": response(packet),
                "source": source(packet),
                "call_control": call_control(packet),
                "semantic": semantic(packet).get("semantic"),
                "target_gap": semantic(packet).get("target_gap"),
                "confirmed_gaps": memory(packet).get("confirmed_gaps"),
                "universal_policy_frame": frame(packet),
                "side_effect_flags": side_effect_flags(packet),
            }
            for packet in packets
        ],
    }


def run_matrix() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for campaign in CAMPAIGNS:
        results.extend(
            [
                validate_active_confirmation(campaign),
                validate_impact_confirmation(campaign),
                validate_appointment_time(campaign),
                validate_weak_impact(campaign),
                validate_repeated_asr_garble(campaign),
            ]
        )
    return results


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    failure_types = Counter()
    by_scenario: dict[str, Counter] = defaultdict(Counter)
    side_effects = {key: False for key in SIDE_EFFECT_KEYS}
    for result in results:
        by_scenario[result["scenario"]]["passed" if result["passed"] else "failed"] += 1
        for failure in result["failures"]:
            failure_types[failure.split(":", 1)[0]] += 1
        for turn in result["turns"]:
            for key, value in (turn.get("side_effect_flags") or {}).items():
                side_effects[key] = bool(side_effects.get(key) or value)
    failures = [result for result in results if not result["passed"]]
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "pass" if not failures else "fail",
        "summary": {
            "matrix_size": len(results),
            "pass_count": len(results) - len(failures),
            "failure_count": len(failures),
            "failure_types": dict(sorted(failure_types.items())),
            "by_scenario": {
                scenario: {"passed": counts.get("passed", 0), "failed": counts.get("failed", 0)}
                for scenario, counts in sorted(by_scenario.items())
            },
            "failure_examples": failures[:10],
        },
        "side_effects": side_effects,
        "results": results,
    }


def write_evidence(result: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        f"# {CHECKPOINT_ID}",
        "",
        f"- Status: `{result['status']}`",
        f"- Matrix size: `{result['summary']['matrix_size']}`",
        f"- Pass count: `{result['summary']['pass_count']}`",
        f"- Failure count: `{result['summary']['failure_count']}`",
        "",
        "## Scenario Summary",
    ]
    for scenario, counts in result["summary"]["by_scenario"].items():
        lines.append(f"- `{scenario}`: `{counts['passed']}` passed / `{counts['failed']}` failed")
    lines.extend(["", "## Side Effects"])
    for key, value in sorted(result["side_effects"].items()):
        lines.append(f"- `{key}`: `{str(value).lower()}`")
    if result["summary"]["failure_examples"]:
        lines.extend(["", "## Failure Examples"])
        for item in result["summary"]["failure_examples"]:
            lines.append(f"- `{item['campaign']}` / `{item['scenario']}`: {item['failures']}")
    (OUT_DIR / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    result = summarize(run_matrix())
    write_evidence(result)
    print(json.dumps({key: result[key] for key in ["checkpoint_id", "status", "summary", "side_effects"]}, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
