"""Validate universal social conversation-management repair.

This focused validator covers buyer friction cues such as speech-rate requests,
repeat requests, language mismatch, name correction, small talk, and frustration.
It uses dry-run turn builders only and asserts that recognized social moves do
not fall back into diagnostic menus, pain inference, wrong-person routing, or
appointment pressure.
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


CHECKPOINT_ID = "UNIVERSAL-SOCIAL-CONVERSATION-MANAGEMENT-001"
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

FULL_MENU_PATTERNS = [
    "missed callbacks, manual tracking, or handoffs",
    "premium or budget, coverage fit, or renewal",
    "manual work, integration, or visibility",
    "vehicle issue, repair timing, or warranty",
    "service need, scheduling urgency, or estimate",
    "service need, scheduling, or estimate",
]

APPOINTMENT_PATTERNS = [
    "callback window",
    "what time",
    "time window",
    "tomorrow",
    "schedule",
    "appointment",
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


def contains_any(text: str, patterns: list[str]) -> bool:
    lower = text.lower()
    return any(pattern in lower for pattern in patterns)


def has_full_menu(text: str) -> bool:
    return contains_any(text, FULL_MENU_PATTERNS)


def has_appointment_ask(text: str) -> bool:
    return contains_any(text, APPOINTMENT_PATTERNS)


def add_failure(failures: list[str], message: str) -> None:
    if message not in failures:
        failures.append(message)


def common_assertions(packet: dict[str, Any], failures: list[str]) -> None:
    for key, value in side_effect_flags(packet).items():
        if value:
            add_failure(failures, f"side effect flag true: {key}")
    text = lower_response(packet)
    for phrase in ["i should", "approved qualified reviewer path", "internal policy", "not the right contact"]:
        if phrase in text:
            add_failure(failures, f"bad customer-facing wording leaked: {phrase}")
    if has_full_menu(text):
        add_failure(failures, "response repeated full menu")
    if has_appointment_ask(text):
        add_failure(failures, "response pushed appointment")
    if semantic(packet).get("semantic") == "pain_confirmed":
        add_failure(failures, "social move inferred pain")
    if source(packet) != "universal_response_shape":
        add_failure(failures, f"source expected universal_response_shape, got {source(packet)}")
    if call_control(packet) != "continue-call":
        add_failure(failures, f"call_control expected continue-call, got {call_control(packet)}")


def assert_move(packet: dict[str, Any], expected: set[str], failures: list[str]) -> None:
    actual = str(frame(packet).get("buyer_move_id") or "")
    if actual not in expected:
        add_failure(failures, f"buyer_move_id expected one of {sorted(expected)}, got {actual}")


def assert_ack(packet: dict[str, Any], labels: list[str], failures: list[str]) -> None:
    if not contains_any(response(packet), labels):
        add_failure(failures, f"response missing acknowledgement cues {labels}")


def assert_gap_preserved(packet: dict[str, Any], expected_gap: str, failures: list[str]) -> None:
    confirmed = list(memory(packet).get("confirmed_gaps") or [])
    current_frame = frame(packet)
    frame_gap = current_frame.get("confirmed_gap_id") or current_frame.get("selected_gap")
    if expected_gap not in confirmed:
        add_failure(failures, f"confirmed_gaps missing {expected_gap}: {confirmed}")
    if frame_gap not in {None, "", expected_gap}:
        add_failure(failures, f"frame gap expected {expected_gap}, got {frame_gap}")


def validate_slow_down(campaign: dict[str, Any]) -> dict[str, Any]:
    packets = run_sequence(campaign, ["__agent_open__", "slow down"], f"{campaign['id']}-slow-down")
    packet = packets[-1]
    failures: list[str] = []
    common_assertions(packet, failures)
    assert_move(packet, {"slow_down_or_speak_faster"}, failures)
    assert_ack(packet, ["slow", "shorter", "simple"], failures)
    return scenario_result(campaign, "slow_down", packets, failures)


def validate_repeat_last_answer(campaign: dict[str, Any]) -> dict[str, Any]:
    packets = run_sequence(campaign, ["__agent_open__", "say that again"], f"{campaign['id']}-repeat")
    packet = packets[-1]
    failures: list[str] = []
    common_assertions(packet, failures)
    assert_move(packet, {"repeat_last_answer", "repeat_or_rephrase_request"}, failures)
    assert_ack(packet, ["sure", "short version", "again"], failures)
    return scenario_result(campaign, "repeat_last_answer", packets, failures)


def validate_language_mismatch(campaign: dict[str, Any]) -> dict[str, Any]:
    packets = run_sequence(campaign, ["__agent_open__", "I don't speak English well"], f"{campaign['id']}-language")
    packet = packets[-1]
    failures: list[str] = []
    common_assertions(packet, failures)
    assert_move(packet, {"language_mismatch"}, failures)
    assert_ack(packet, ["simple", "english", "understood", "no problem"], failures)
    return scenario_result(campaign, "language_mismatch", packets, failures)


def validate_frustration(campaign: dict[str, Any]) -> dict[str, Any]:
    packets = run_sequence(campaign, ["__agent_open__", "you're annoying"], f"{campaign['id']}-frustration")
    packet = packets[-1]
    failures: list[str] = []
    common_assertions(packet, failures)
    assert_move(packet, {"emotional_frustration", "abusive_or_hostile_buyer"}, failures)
    assert_ack(packet, ["fair", "understood", "sorry", "waste your time"], failures)
    return scenario_result(campaign, "frustration", packets, failures)


def validate_social_after_pain(campaign: dict[str, Any]) -> dict[str, Any]:
    packets = run_sequence(
        campaign,
        ["__agent_open__", "yeah sure", campaign["pain"], "slow down"],
        f"{campaign['id']}-social-after-pain",
    )
    packet = packets[-1]
    failures: list[str] = []
    common_assertions(packet, failures)
    assert_move(packet, {"slow_down_or_speak_faster"}, failures)
    assert_ack(packet, ["slow", "shorter", "simple"], failures)
    assert_gap_preserved(packet, campaign["expected_gap"], failures)
    return scenario_result(campaign, "social_after_pain", packets, failures)


def validate_frustration_after_repeated_question(campaign: dict[str, Any]) -> dict[str, Any]:
    packets = run_sequence(
        campaign,
        ["__agent_open__", "yeah sure", campaign["pain"], "what do you mean", "you're annoying"],
        f"{campaign['id']}-frustration-after-challenge",
    )
    packet = packets[-1]
    failures: list[str] = []
    common_assertions(packet, failures)
    assert_move(packet, {"emotional_frustration", "abusive_or_hostile_buyer"}, failures)
    assert_ack(packet, ["fair", "understood", "sorry", "waste your time"], failures)
    if "already answered" in lower_response(packet) or "concrete follow-up" in lower_response(packet):
        add_failure(failures, "frustration triggered duplicate-answer repair")
    return scenario_result(campaign, "frustration_after_repeated_question", packets, failures)


def validate_small_talk(campaign: dict[str, Any]) -> dict[str, Any]:
    packets = run_sequence(campaign, ["__agent_open__", "haha okay"], f"{campaign['id']}-small-talk")
    packet = packets[-1]
    failures: list[str] = []
    common_assertions(packet, failures)
    assert_move(packet, {"small_talk", "silence_or_backchannel"}, failures)
    assert_ack(packet, ["okay", "quick", "thanks", "sure"], failures)
    return scenario_result(campaign, "small_talk_backchannel", packets, failures)


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
                validate_slow_down(campaign),
                validate_repeat_last_answer(campaign),
                validate_language_mismatch(campaign),
                validate_frustration(campaign),
                validate_social_after_pain(campaign),
                validate_frustration_after_repeated_question(campaign),
                validate_small_talk(campaign),
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
