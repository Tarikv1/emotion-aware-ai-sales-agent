"""Validate close-strength and low-impact exit wording.

This focused checkpoint covers wording quality after appointment readiness:
high-readiness closes should acknowledge impact and ask one concrete next step,
while weak-impact exits should reduce pressure without sounding defeated. It
uses dry-run turn builders only and performs no provider, live TTS, email,
calendar, CRM, or PROD-102 actions.
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

from scripts import generate_commercial_sales_conversation_review_packet_001 as review_packet  # noqa: E402
from scripts import run_live_demo_001_agent_voice_call as demo  # noqa: E402


CHECKPOINT_ID = "UNIVERSAL-CLOSE-STRENGTH-001"
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

ACK_PREFIXES = ("got it", "understood", "that makes sense")
SEND_INFO_ACKS = ("sure", "understood", "got it")
NEXT_STEP_PATTERNS = (
    "callback window",
    "time window",
    "what time",
    "what day",
    "which day",
    "preferred window",
    "what works",
    "what email",
    "email should",
    "email or callback",
)
CONTACT_PATH_PATTERNS = (
    "what email",
    "email should",
    "email or callback",
    "callback window",
    "contact",
)
FULL_MENU_PATTERNS = (
    "missed callbacks, manual tracking, or handoffs",
    "owner, callback reminder, or handoff",
    "premium or budget, coverage fit, or renewal",
    "premium, coverage fit, or renewal",
    "manual work, integration, or visibility",
    "vehicle issue, repair timing, or warranty",
    "service need, scheduling urgency, or estimate",
    "service need, scheduling, or estimate",
)
WEAK_HIGH_READINESS_PATTERNS = (
    "probably",
    "maybe",
    "would a review be useful",
    "we can leave it there",
    "should i stop",
)
FAKE_SIDE_EFFECT_CLAIMS = (
    "i sent",
    "i have sent",
    "i'll send",
    "i will send",
    "calendar invite",
    "booked",
    "scheduled it",
    "crm",
)
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
    append_state(state, packet)
    return packet


def run_sequence(campaign: dict[str, Any], turns: list[str], session_id: str) -> list[dict[str, Any]]:
    state: dict[str, Any] = {}
    return [build_turn(turn, state, campaign, session_id) for turn in turns]


def slug(text: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in text.lower()).strip("-")


def response(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("final_response") or packet.get("final_response") or "")


def frame(packet: dict[str, Any]) -> dict[str, Any]:
    return packet.get("universal_policy_frame") or (packet.get("dialogue_manager") or {}).get("universal_policy_frame") or {}


def memory(packet: dict[str, Any]) -> dict[str, Any]:
    return packet.get("conversation_memory") or packet.get("demo_conversation_memory") or {}


def call_control(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("call_control") or "")


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


def review_warnings(packet: dict[str, Any], buyer_utterance: str) -> list[str]:
    return review_packet.mechanical_warning_flags(
        buyer_utterance=buyer_utterance,
        response=response(packet),
        frame=frame(packet),
        flags=side_effect_flags(packet),
    )


def contains_any(text: str, patterns: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(pattern in lowered for pattern in patterns)


def starts_with_any(text: str, patterns: tuple[str, ...]) -> bool:
    stripped = text.lower().strip()
    return any(stripped.startswith(pattern) for pattern in patterns)


def add_failure(failures: list[str], message: str) -> None:
    if message not in failures:
        failures.append(message)


def common_assertions(packet: dict[str, Any], failures: list[str]) -> None:
    text = response(packet)
    lowered = text.lower()
    for key, value in side_effect_flags(packet).items():
        if value:
            add_failure(failures, f"side effect flag true: {key}")
    if contains_any(lowered, FULL_MENU_PATTERNS):
        add_failure(failures, "full diagnostic menu repeated")
    if contains_any(lowered, FAKE_SIDE_EFFECT_CLAIMS):
        add_failure(failures, "fake email/calendar/CRM claim")
    for phrase in ("i should", "approved qualified reviewer path", "approved scope here", "internal policy"):
        if phrase in lowered:
            add_failure(failures, f"internal wording leaked: {phrase}")


def expect_gap_preserved(packet: dict[str, Any], campaign: dict[str, Any], failures: list[str]) -> None:
    current = frame(packet)
    confirmed = set(memory(packet).get("confirmed_gaps") or [])
    candidates = {
        str(current.get("confirmed_gap_id") or ""),
        str(current.get("selected_gap") or ""),
        *confirmed,
    }
    if campaign["expected_gap"] not in candidates:
        add_failure(failures, f"expected gap {campaign['expected_gap']} not preserved; got {sorted(candidates)}")


def scenario_turns(label: str, campaign: dict[str, Any]) -> list[str]:
    ready_path = ["__agent_open__", "yeah sure", campaign["pain"], "it wastes time"]
    return {
        "high_readiness_close": ready_path,
        "send_info_after_readiness": [*ready_path, "send me details"],
        "weak_impact_exit": ["__agent_open__", "yeah sure", campaign["pain"], "not really, just annoying"],
        "frustration_preservation": ["__agent_open__", "yeah sure", campaign["pain"], "you're annoying"],
        "concrete_time_preservation": [*ready_path, "tomorrow at 3 works"],
    }[label]


def evaluate_scenario(label: str, campaign: dict[str, Any], packets: list[dict[str, Any]]) -> dict[str, Any]:
    packet = packets[-1]
    buyer_utterance = scenario_turns(label, campaign)[-1]
    current = frame(packet)
    text = response(packet)
    lowered = text.lower()
    warnings = review_warnings(packet, buyer_utterance)
    failures: list[str] = []
    common_assertions(packet, failures)

    if label == "high_readiness_close":
        if current.get("buyer_move_id") != "implication_confirmed":
            add_failure(failures, f"expected implication_confirmed, got {current.get('buyer_move_id')}")
        if current.get("appointment_readiness") not in {"high", "medium"}:
            add_failure(failures, f"readiness not high/medium: {current.get('appointment_readiness')}")
        if not starts_with_any(text, ACK_PREFIXES):
            add_failure(failures, "high-readiness response did not start with acknowledgement")
        if not contains_any(lowered, NEXT_STEP_PATTERNS):
            add_failure(failures, "high-readiness response did not ask callback/time-window next step")
        if contains_any(lowered, WEAK_HIGH_READINESS_PATTERNS):
            add_failure(failures, "weak high-readiness close language used")
        if text.count("?") > 1:
            add_failure(failures, "high-readiness response asked more than one question")
        if "no_acknowledgement" in warnings:
            add_failure(failures, "no_acknowledgement warning present")
        if call_control(packet) != "continue-call":
            add_failure(failures, f"expected continue-call, got {call_control(packet)}")
    elif label == "send_info_after_readiness":
        if current.get("buyer_move_id") != "send_info_request":
            add_failure(failures, f"expected send_info_request, got {current.get('buyer_move_id')}")
        if current.get("appointment_readiness") not in {"high", "medium"}:
            add_failure(failures, f"readiness lost after send-info: {current.get('appointment_readiness')}")
        expect_gap_preserved(packet, campaign, failures)
        if not starts_with_any(text, SEND_INFO_ACKS):
            add_failure(failures, "send-info response did not acknowledge request")
        if not contains_any(lowered, CONTACT_PATH_PATTERNS):
            add_failure(failures, "send-info response did not ask email/contact/callback path")
        if "already sounds worth review" in lowered:
            add_failure(failures, "send-info after readiness used awkward worth-review phrasing")
        if text.count("?") > 1:
            add_failure(failures, "send-info response asked more than one question")
    elif label == "weak_impact_exit":
        if current.get("buyer_move_id") != "implication_weak_or_denied":
            add_failure(failures, f"expected implication_weak_or_denied, got {current.get('buyer_move_id')}")
        if current.get("appointment_readiness") != "low":
            add_failure(failures, f"expected low readiness, got {current.get('appointment_readiness')}")
        if contains_any(lowered, NEXT_STEP_PATTERNS):
            add_failure(failures, "weak impact received appointment pressure")
        if "we can leave it there" in lowered or "i can stop here" in lowered:
            add_failure(failures, "weak impact used defeated stop/leave wording")
        if "over_deferential_stop_offer" in warnings:
            add_failure(failures, "over_deferential_stop_offer warning present")
        if not any(phrase in lowered for phrase in ("no reason to force", "would not push", "will not push")):
            add_failure(failures, "weak impact response lacked low-pressure authority")
    elif label == "frustration_preservation":
        if current.get("buyer_move_id") not in {"emotional_frustration", "abusive_or_hostile_buyer"}:
            add_failure(failures, f"expected frustration move, got {current.get('buyer_move_id')}")
        if contains_any(lowered, NEXT_STEP_PATTERNS):
            add_failure(failures, "frustration received appointment pressure")
        if not any(phrase in lowered for phrase in ("fair", "understood", "waste your time", "annoying", "frustrating", "end the call")):
            add_failure(failures, "frustration response did not de-escalate")
    elif label == "concrete_time_preservation":
        if current.get("buyer_move_id") != "callback_time_provided":
            add_failure(failures, f"expected callback_time_provided, got {current.get('buyer_move_id')}")
        expect_gap_preserved(packet, campaign, failures)
        if call_control(packet) not in {"schedule-and-end", "continue-call"}:
            add_failure(failures, f"unexpected call_control for concrete time: {call_control(packet)}")
        if "appointment_not_asked_when_ready" in warnings:
            add_failure(failures, "appointment_not_asked_when_ready warning present")

    return {
        "scenario": label,
        "campaign_id": campaign["id"],
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "buyer_utterance": buyer_utterance,
        "buyer_move_id": current.get("buyer_move_id"),
        "appointment_readiness": current.get("appointment_readiness"),
        "next_best_sales_action": current.get("next_best_sales_action"),
        "confirmed_gaps": memory(packet).get("confirmed_gaps"),
        "call_control": call_control(packet),
        "source": source(packet),
        "final_response": text,
        "mechanical_warning_flags": warnings,
        "universal_policy_frame": current,
        "side_effect_flags": side_effect_flags(packet),
    }


def write_evidence(results: list[dict[str, Any]]) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    failures = [row for row in results if row["status"] != "pass"]
    by_scenario: dict[str, dict[str, int]] = defaultdict(lambda: {"passed": 0, "failed": 0})
    failure_types: Counter[str] = Counter()
    warning_counts: Counter[str] = Counter()
    side_effects = {key: False for key in SIDE_EFFECT_KEYS}
    before_after_examples: dict[str, dict[str, str]] = {}
    for row in results:
        by_scenario[row["scenario"]]["passed" if row["status"] == "pass" else "failed"] += 1
        for failure in row["failures"]:
            failure_types[failure] += 1
        warning_counts.update(row.get("mechanical_warning_flags") or [])
        for key, value in (row.get("side_effect_flags") or {}).items():
            side_effects[key] = bool(side_effects.get(key) or value)
        before_after_examples.setdefault(
            row["scenario"],
            {
                "campaign_id": row["campaign_id"],
                "final_response": row["final_response"],
            },
        )
    summary = {
        "matrix_size": len(results),
        "pass_count": len(results) - len(failures),
        "failure_count": len(failures),
        "by_scenario": dict(sorted(by_scenario.items())),
        "failure_types": dict(failure_types.most_common()),
        "mechanical_warning_counts": dict(sorted(warning_counts.items())),
        "failure_examples": failures[:10],
    }
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "pass" if not failures else "fail",
        "summary": summary,
        "results": results,
        "before_after_examples": before_after_examples,
        "side_effects": side_effects,
        "provider_calls_made": False,
        "local_llm_calls_made": False,
        "live_tts_used": False,
        "sends_email": False,
        "creates_calendar_event": False,
        "writes_crm": False,
        "opens_prod_102": False,
        "runtime_behavior_changed": True,
    }
    (OUT_DIR / "result.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        f"# {CHECKPOINT_ID}",
        "",
        "## Summary",
        f"- Status: `{payload['status']}`",
        f"- Matrix size: `{summary['matrix_size']}`",
        f"- Pass count: `{summary['pass_count']}`",
        f"- Failure count: `{summary['failure_count']}`",
        "",
        "## Scenario Summary",
    ]
    for scenario, counts in sorted(by_scenario.items()):
        lines.append(f"- `{scenario}`: `{counts['passed']}` passed / `{counts['failed']}` failed")
    lines.extend(["", "## Mechanical Warning Counts"])
    if warning_counts:
        for key, value in sorted(warning_counts.items()):
            lines.append(f"- `{key}`: `{value}`")
    else:
        lines.append("- None")
    lines.extend(["", "## Representative Responses"])
    for scenario, example in sorted(before_after_examples.items()):
        lines.append(f"- `{scenario}` / `{example['campaign_id']}`: {example['final_response']}")
    lines.extend(["", "## Failure Types"])
    if failure_types:
        for key, value in failure_types.most_common():
            lines.append(f"- `{key}`: `{value}`")
    else:
        lines.append("- None")
    lines.extend(["", "## Side Effects"])
    for key, value in sorted(side_effects.items()):
        lines.append(f"- `{key}`: `{str(value).lower()}`")
    (OUT_DIR / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    scenarios = [
        "high_readiness_close",
        "send_info_after_readiness",
        "weak_impact_exit",
        "frustration_preservation",
        "concrete_time_preservation",
    ]
    results: list[dict[str, Any]] = []
    for campaign in CAMPAIGNS:
        for scenario in scenarios:
            session_id = f"{CHECKPOINT_ID}-{campaign['id']}-{slug(scenario)}"
            packets = run_sequence(campaign, scenario_turns(scenario, campaign), session_id)
            results.append(evaluate_scenario(scenario, campaign, packets))
    payload = write_evidence(results)
    print(json.dumps({key: payload[key] for key in ("checkpoint_id", "status", "summary", "side_effects")}, indent=2))
    if payload["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
