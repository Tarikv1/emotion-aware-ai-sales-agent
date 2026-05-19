#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from statistics import mean
from typing import Any

if str(ROOT := Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_live_demo_001_agent_voice_call import DEFAULT_CASES_PATH, DEFAULT_PRIVATE_OUT, build_turn_packet  # noqa: E402

CHECKPOINT_ID = "LIVE-DEMO-003-supervised-live-voice-acceptance"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
DEFAULT_PACKET_OUT = GENERATED_DIR / "acceptance_packet.json"
DEFAULT_REPORT_OUT = GENERATED_DIR / "acceptance_report.md"
DEFAULT_REVIEW_FORM_OUT = GENERATED_DIR / "manual_review_form.md"
DEFAULT_REVIEW_CSV_OUT = GENERATED_DIR / "manual_review.csv"
DEFAULT_CAMPAIGN_ID = "campaign-prod-005-b2b-software"
DEFAULT_STAGE = "relevance-check"

TERMINAL_CALL_CONTROLS = {"end-call", "hang-up", "schedule-and-end", "close-and-log-sale-ready", "transfer-or-escalate"}
INTERNAL_WORDING_BLOCKLIST = ["runtime", "guardrail", "anti-loop", "decision log", "same question"]

RECOMMENDED_SPOKEN_TEST_PATH = [
    {"step": 1, "speaker": "agent", "prompt": "Start Conversation", "purpose": "agent opening"},
    {"step": 2, "speaker": "buyer", "prompt": "hmm okay", "purpose": "vague acknowledgement"},
    {"step": 3, "speaker": "buyer", "prompt": "I didn't understand what you asked", "purpose": "previous-question clarification"},
    {"step": 4, "speaker": "buyer", "prompt": "callbacks are probably the problem", "purpose": "callback workflow gap"},
    {"step": 5, "speaker": "buyer", "prompt": "what do you mean by callbacks?", "purpose": "callback definition"},
    {"step": 6, "speaker": "buyer", "prompt": "tell me more", "purpose": "follow-up continuity"},
    {"step": 7, "speaker": "buyer", "prompt": "why does that matter?", "purpose": "value mapping"},
    {"step": 8, "speaker": "buyer", "prompt": "what does it cost?", "purpose": "price question"},
    {"step": 9, "speaker": "buyer", "prompt": "I am not sure it fits our workflow", "purpose": "fit objection"},
    {"step": 10, "speaker": "buyer", "prompt": "no", "purpose": "ambiguous negative"},
    {"step": 11, "speaker": "buyer", "prompt": "what next?", "purpose": "safe next step"},
    {"step": 12, "speaker": "buyer", "prompt": "call me back later", "purpose": "callback scheduling request"},
    {"step": 13, "speaker": "buyer", "prompt": "tomorrow at 3 works", "purpose": "callback time confirmation after scheduling context"},
]

OPTIONAL_STRESS_TURNS = [
    "you called me",
    "I don't have a question",
    "I don't know what you're talking about",
    "does it replace my CRM?",
    "does it have SOC 2?",
    "send me a short summary",
    "tomorrow at 3 works",
]

SYNTHETIC_TRANSCRIPTS = [
    "__agent_open__",
    "hmm okay",
    "I didn't understand what you asked",
    "callbacks are probably the problem",
    "what do you mean by callbacks?",
    "tell me more",
    "why does that matter?",
    "what does it cost?",
    "I am not sure it fits our workflow",
    "no",
    "what next?",
    "call me back later",
    "tomorrow at 3 works",
]

MANUAL_REVIEW_FIELDS = [
    "asr_captured_correctly",
    "agent_interrupted_or_talked_over_user",
    "turn_taking_felt_natural",
    "response_latency_felt_acceptable",
    "voice_consistency",
    "response_naturalness",
    "sales_steering",
    "repeated_itself",
    "echoed_customer_too_much",
    "callback_confusion_seen",
    "buyer_agency_preserved",
    "notes",
    "accepted_for_next_iteration",
]

MANUAL_REVIEW_FIELD_HELP = {
    "asr_captured_correctly": "true, false, or unclear: did the transcript match what you said?",
    "agent_interrupted_or_talked_over_user": "true if the agent started while you were still speaking.",
    "turn_taking_felt_natural": "1-5: did listen/speak timing feel natural?",
    "response_latency_felt_acceptable": "1-5: did the delay feel acceptable?",
    "voice_consistency": "1-5: did the same voice/style stay consistent?",
    "response_naturalness": "1-5: did the response sound natural?",
    "sales_steering": "1-5: did the agent guide toward a useful sales next step?",
    "repeated_itself": "true if it repeated the same answer or question.",
    "echoed_customer_too_much": "true if it mirrored your sentence instead of advancing.",
    "callback_confusion_seen": "true if workflow callbacks were confused with scheduling.",
    "buyer_agency_preserved": "true if the agent respected stop/no/later boundaries.",
    "notes": "short free-text note for the turn.",
    "accepted_for_next_iteration": "true only if this turn is acceptable for the next iteration.",
}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def manual_review_template() -> dict[str, Any]:
    return {
        "asr_captured_correctly": None,
        "agent_interrupted_or_talked_over_user": None,
        "turn_taking_felt_natural": None,
        "response_latency_felt_acceptable": None,
        "voice_consistency": None,
        "response_naturalness": None,
        "sales_steering": None,
        "repeated_itself": None,
        "echoed_customer_too_much": None,
        "callback_confusion_seen": None,
        "buyer_agency_preserved": None,
        "notes": "",
        "accepted_for_next_iteration": None,
    }


def parse_bool(value: str) -> bool | str | None:
    normalized = str(value or "").strip().lower()
    if normalized in {"", "none", "null"}:
        return None
    if normalized in {"true", "yes", "y", "1"}:
        return True
    if normalized in {"false", "no", "n", "0"}:
        return False
    if normalized == "unclear":
        return "unclear"
    raise ValueError(f"Expected boolean or unclear, got {value!r}.")


def parse_score(value: str) -> int | None:
    normalized = str(value or "").strip()
    if not normalized:
        return None
    score = int(normalized)
    if score < 1 or score > 5:
        raise ValueError(f"Expected 1-5 score, got {value!r}.")
    return score


def parse_manual_review_row(row: dict[str, str]) -> dict[str, Any]:
    review = manual_review_template()
    review["asr_captured_correctly"] = parse_bool(row.get("asr_captured_correctly", ""))
    for field in [
        "agent_interrupted_or_talked_over_user",
        "repeated_itself",
        "echoed_customer_too_much",
        "callback_confusion_seen",
        "buyer_agency_preserved",
        "accepted_for_next_iteration",
    ]:
        value = parse_bool(row.get(field, ""))
        if value == "unclear":
            raise ValueError(f"{field} must be true or false, not unclear.")
        review[field] = value
    for field in [
        "turn_taking_felt_natural",
        "response_latency_felt_acceptable",
        "voice_consistency",
        "response_naturalness",
        "sales_steering",
    ]:
        review[field] = parse_score(row.get(field, ""))
    review["notes"] = str(row.get("notes") or "")
    return review


def apply_manual_review_csv(packet: dict[str, Any], csv_path: Path) -> None:
    rows = list(csv.DictReader(csv_path.read_text(encoding="utf-8").splitlines()))
    reviews_by_turn = {str(row.get("turn_index") or "").strip(): parse_manual_review_row(row) for row in rows}
    for turn in packet.get("turns", []):
        key = str(turn.get("turn_index") or "")
        if key in reviews_by_turn:
            turn["manual_review"] = reviews_by_turn[key]


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(text or "").lower()).strip()


def full_customer_echo_violation(transcript: str, response: str) -> bool:
    customer = normalize(transcript)
    spoken = normalize(response)
    if not customer or not spoken or customer == "agent open":
        return False
    words = customer.split()
    if len(words) >= 4 and spoken.startswith(" ".join(words[: min(len(words), 7)])):
        return True
    return len(words) >= 5 and customer in spoken


def asks_for_callback_time(response: str) -> bool:
    lowered = response.lower()
    return any(fragment in lowered for fragment in ["what time", "when should", "time should i note", "note for the callback"])


def workflow_callback_treated_as_scheduling(turn: dict[str, Any]) -> bool:
    transcript = normalize(turn.get("transcript", ""))
    if not any(fragment in transcript for fragment in ["callbacks", "callback reminders", "missed callbacks"]):
        return False
    if any(fragment in transcript for fragment in ["call me", "call back", "callback later"]):
        return False
    return asks_for_callback_time(str(turn.get("final_response") or ""))


def internal_wording_leaked(response: str) -> bool:
    lowered = response.lower()
    return any(fragment in lowered for fragment in INTERNAL_WORDING_BLOCKLIST)


def turn_from_packet(packet: dict[str, Any]) -> dict[str, Any]:
    summary = packet.get("summary", {})
    tts_delivery = (packet.get("packet") or {}).get("tts_delivery", {})
    async_packet = packet.get("dialogue_reasoner_async_enrichment", {})
    provider_tts_used = bool(summary.get("tts_provider_calls_made"))
    audio_created = bool(summary.get("tts_audio_file_created"))
    return {
        "turn_index": packet.get("session_turn_index"),
        "source_live_demo_id": packet.get("live_demo_id"),
        "transcript": packet.get("transcript"),
        "input_type": packet.get("input_type"),
        "asr_confidence": (packet.get("asr") or {}).get("confidence"),
        "asr_quality_gate": (packet.get("asr") or {}).get("quality_gate"),
        "audio_uploaded_to_python_server": (packet.get("asr") or {}).get("audio_uploaded_to_python_server"),
        "browser_vendor_may_process_audio": (packet.get("asr") or {}).get("browser_vendor_may_process_audio"),
        "final_response": summary.get("final_response"),
        "call_control": summary.get("call_control"),
        "demo_conversation_memory": packet.get("demo_conversation_memory", {}),
        "demo_conversation_stability_guard": packet.get("demo_conversation_stability_guard", {}),
        "async_enrichment_boundary_packet": async_packet,
        "server_latency_ms": (packet.get("latency") or {}).get("server_total_ms"),
        "tts_latency_ms": summary.get("total_provider_latency_ms"),
        "tts_time_to_first_audio_ms": summary.get("time_to_first_audio_ms"),
        "provider_tts_used": provider_tts_used,
        "browser_fallback_voice_used": not audio_created,
        "tts_audio_file_created": audio_created,
        "tts_fallback_reason": summary.get("tts_fallback_reason"),
        "tts_input_source": summary.get("tts_input_source"),
        "voice_delivery_validation_passed": ((packet.get("packet") or {}).get("voice_delivery") or {}).get("validation", {}).get("passed"),
        "tts_delivery_validation_passed": tts_delivery.get("validation", {}).get("passed"),
        "provider_agent_used": packet.get("provider_agent_used"),
        "durable_provider_agent_created": packet.get("durable_provider_agent_created"),
        "voice_cloning_used": packet.get("voice_cloning_used"),
        "opens_prod_102": packet.get("opens_prod_102"),
        "manual_review": manual_review_template(),
    }


def append_session_turn(session_state: dict[str, Any], packet: dict[str, Any]) -> None:
    session_state.setdefault("turns", []).append(
        {
            "transcript": packet.get("transcript"),
            "summary": packet.get("summary", {}),
            "continuity": packet.get("demo_session_continuity", {}),
            "conversation_memory": packet.get("demo_conversation_memory", {}),
        }
    )


def build_synthetic_turns(args: argparse.Namespace) -> list[dict[str, Any]]:
    session_state: dict[str, Any] = {"turns": []}
    private_out = Path(args.private_out).resolve()
    turns = []
    for transcript in SYNTHETIC_TRANSCRIPTS:
        packet = build_turn_packet(
            transcript=transcript,
            campaign_id=args.campaign,
            stage=args.stage,
            input_type="agent-open" if transcript == "__agent_open__" else "speech-final",
            silence_count=0,
            cases_path=Path(args.cases).resolve(),
            private_out=private_out,
            live_tts=args.live_tts,
            force_key_missing=args.force_key_missing,
            timeout_seconds=args.timeout_seconds,
            session_id=args.session_id,
            session_state=session_state,
            asr_confidence=None,
            voice_turn_state="idle",
        )
        turns.append(turn_from_packet(packet))
        append_session_turn(session_state, packet)
    return turns


def load_private_turns(private_turns_dir: Path, session_id: str | None = None) -> list[dict[str, Any]]:
    paths = sorted(private_turns_dir.glob("LIVE-DEMO-001-turn-*.json"))
    turns = []
    for path in paths:
        packet = json.loads(path.read_text(encoding="utf-8"))
        if session_id and str(packet.get("session_id")) != session_id:
            continue
        turn = turn_from_packet(packet)
        try:
            turn["source_private_turn_json"] = str(path.relative_to(ROOT))
        except ValueError:
            turn["source_private_turn_json"] = str(path)
        turns.append(turn)
    return turns


def hard_gate_results(turns: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    responses = [str(turn.get("final_response") or "") for turn in turns]
    call_controls = [str(turn.get("call_control") or "") for turn in turns]
    explicit_callback_turns = [turn for turn in turns if "call me back later" in normalize(turn.get("transcript", ""))]
    terminal_turns = [turn for turn in turns if str(turn.get("call_control") or "") in TERMINAL_CALL_CONTROLS]
    return {
        "no_provider_hosted_durable_agent": {
            "passed": all(turn.get("durable_provider_agent_created") is False and turn.get("provider_agent_used") is False for turn in turns),
            "required": True,
        },
        "no_voice_cloning": {"passed": all(turn.get("voice_cloning_used") is False for turn in turns), "required": True},
        "no_customer_audio_upload_to_python_server": {
            "passed": all(turn.get("audio_uploaded_to_python_server") is False for turn in turns),
            "required": True,
        },
        "no_llm_blocking_live_spoken_response": {
            "passed": all((turn.get("async_enrichment_boundary_packet") or {}).get("customer_response_snapshot", {}).get("available_before_provider") is True for turn in turns),
            "required": True,
        },
        "no_llm_mutation_of_final_response": {
            "passed": all((turn.get("async_enrichment_boundary_packet") or {}).get("mutates_final_response") is False for turn in turns),
            "required": True,
        },
        "no_payment_collection": {
            "passed": not any(any(fragment in response.lower() for fragment in ["card number", "payment", "checkout", "contract signing"]) for response in responses),
            "required": True,
        },
        "no_bare_workflow_callback_treated_as_scheduling": {
            "passed": not any(workflow_callback_treated_as_scheduling(turn) for turn in turns),
            "required": True,
        },
        "explicit_call_me_back_later_still_schedules": {
            "passed": bool(explicit_callback_turns) and all(asks_for_callback_time(str(turn.get("final_response") or "")) for turn in explicit_callback_turns),
            "required": True,
        },
        "terminal_call_control_stops_listening_restart": {
            "passed": bool(terminal_turns) and "schedule-and-end" in call_controls,
            "required": True,
            "evidence": "Browser runner treats schedule-and-end as terminal and does not restart listening.",
        },
        "no_exact_repeated_final_response": {"passed": len(responses) == len(set(responses)), "required": True},
        "no_obvious_customer_sentence_echoing": {
            "passed": not any(full_customer_echo_violation(str(turn.get("transcript") or ""), str(turn.get("final_response") or "")) for turn in turns),
            "required": True,
        },
        "no_internal_wording_leaked": {"passed": not any(internal_wording_leaked(response) for response in responses), "required": True},
    }


def human_quality_gate_defaults() -> dict[str, Any]:
    return {
        "turn_taking_average_min": 4,
        "latency_acceptability_average_min": 4,
        "voice_consistency_average_min": 4,
        "response_naturalness_average_min": 3,
        "sales_steering_average_min": 4,
        "buyer_agency_preserved_required": True,
        "accepted_for_next_iteration_required": True,
    }


def numeric_average(reviews: list[dict[str, Any]], field: str) -> float | None:
    values = [review.get(field) for review in reviews if isinstance(review.get(field), (int, float))]
    return mean(values) if values else None


def manual_review_complete(reviews: list[dict[str, Any]]) -> bool:
    required = [field for field in MANUAL_REVIEW_FIELDS if field != "notes"]
    return bool(reviews) and all(review.get(field) is not None for review in reviews for field in required)


def evaluate_acceptance(packet: dict[str, Any]) -> dict[str, Any]:
    turns = list(packet.get("turns") or [])
    hard_gates = hard_gate_results(turns)
    human_gates = human_quality_gate_defaults()
    reviews = [turn.get("manual_review") or {} for turn in turns]
    hard_failures = [name for name, gate in hard_gates.items() if gate.get("required") and not gate.get("passed")]
    if not manual_review_complete(reviews):
        return {
            "status": "pending_manual_review" if not hard_failures else "not_accepted",
            "accepted": False,
            "hard_gate_failures": hard_failures,
            "human_gate_failures": ["manual_review_incomplete"],
            "averages": {},
            "recommendation": "Run the supervised live call and fill every manual review field before accepting LIVE-DEMO-003.",
        }

    averages = {
        "turn_taking_felt_natural": numeric_average(reviews, "turn_taking_felt_natural"),
        "response_latency_felt_acceptable": numeric_average(reviews, "response_latency_felt_acceptable"),
        "voice_consistency": numeric_average(reviews, "voice_consistency"),
        "response_naturalness": numeric_average(reviews, "response_naturalness"),
        "sales_steering": numeric_average(reviews, "sales_steering"),
    }
    human_failures = []
    if (averages["turn_taking_felt_natural"] or 0) < human_gates["turn_taking_average_min"]:
        human_failures.append("turn_taking_average_below_4")
    if (averages["response_latency_felt_acceptable"] or 0) < human_gates["latency_acceptability_average_min"]:
        human_failures.append("latency_acceptability_average_below_4")
    if (averages["voice_consistency"] or 0) < human_gates["voice_consistency_average_min"]:
        human_failures.append("voice_consistency_average_below_4")
    if (averages["response_naturalness"] or 0) < human_gates["response_naturalness_average_min"]:
        human_failures.append("response_naturalness_average_below_3")
    if (averages["sales_steering"] or 0) < human_gates["sales_steering_average_min"]:
        human_failures.append("sales_steering_average_below_4")
    if not all(review.get("buyer_agency_preserved") is True for review in reviews):
        human_failures.append("buyer_agency_not_preserved")
    if not all(review.get("accepted_for_next_iteration") is True for review in reviews):
        human_failures.append("manual_not_accepted_for_next_iteration")
    if any(review.get("agent_interrupted_or_talked_over_user") is True for review in reviews):
        human_failures.append("agent_talked_over_user")
    if any(review.get("repeated_itself") is True for review in reviews):
        human_failures.append("manual_repetition_seen")
    if any(review.get("echoed_customer_too_much") is True for review in reviews):
        human_failures.append("manual_echo_seen")
    if any(review.get("callback_confusion_seen") is True for review in reviews):
        human_failures.append("manual_callback_confusion_seen")

    accepted = not hard_failures and not human_failures
    return {
        "status": "accepted_for_next_iteration" if accepted else "not_accepted",
        "accepted": accepted,
        "hard_gate_failures": hard_failures,
        "human_gate_failures": human_failures,
        "averages": averages,
        "recommendation": (
            "Proceed to the next narrow live-voice iteration checkpoint."
            if accepted
            else "Create a narrow follow-up checkpoint from the failed gates; do not rewrite the runtime broadly."
        ),
    }


def build_packet(turns: list[dict[str, Any]], args: argparse.Namespace) -> dict[str, Any]:
    packet = {
        "checkpoint_id": CHECKPOINT_ID,
        "purpose": "Human-supervised live voice acceptance after LIVE-DEMO-002 text/runtime validation.",
        "demo_session_id": args.session_id,
        "campaign_id": args.campaign,
        "stage": args.stage,
        "live_tts_enabled": bool(args.live_tts or any(turn.get("provider_tts_used") for turn in turns)),
        "browser_fallback_voice_used": any(turn.get("browser_fallback_voice_used") is True for turn in turns),
        "asr_used": any(str(turn.get("input_type") or "") != "agent-open" for turn in turns),
        "provider_tts_used": any(turn.get("provider_tts_used") is True for turn in turns),
        "llm_enrichment_enabled": False,
        "provider_llm_call_occurred": any((turn.get("async_enrichment_boundary_packet") or {}).get("provider_call_made") is True for turn in turns),
        "durable_provider_agent_created": any(turn.get("durable_provider_agent_created") is True for turn in turns),
        "voice_cloning_used": any(turn.get("voice_cloning_used") is True for turn in turns),
        "payment_collection_enabled": False,
        "production_readiness_claimed": False,
        "opens_prod_102": False,
        "manual_review_schema": {
            "fields": MANUAL_REVIEW_FIELDS,
            "field_help": MANUAL_REVIEW_FIELD_HELP,
            "scale": "1-5 where applicable; booleans must be true/false; use unclear only for asr_captured_correctly if needed.",
        },
        "recommended_spoken_test_path": RECOMMENDED_SPOKEN_TEST_PATH,
        "optional_stress_turns": OPTIONAL_STRESS_TURNS,
        "scenario_note": "The recommended and stress turns are sample scenarios only, not runtime caps.",
        "turns": turns,
    }
    packet["hard_gates"] = hard_gate_results(turns)
    packet["human_quality_gates"] = human_quality_gate_defaults()
    packet["acceptance_result"] = evaluate_acceptance(packet)
    return packet


def render_report(packet: dict[str, Any]) -> str:
    result = packet["acceptance_result"]
    lines = [
        "# LIVE-DEMO-003 Supervised Live Voice Acceptance",
        "",
        f"- Checkpoint: `{packet['checkpoint_id']}`",
        f"- Demo session: `{packet['demo_session_id']}`",
        f"- Campaign: `{packet['campaign_id']}`",
        f"- Acceptance status: `{result['status']}`",
        f"- Provider TTS used: `{str(packet['provider_tts_used']).lower()}`",
        f"- Provider LLM call occurred: `{str(packet['provider_llm_call_occurred']).lower()}`",
        f"- Browser fallback voice used: `{str(packet['browser_fallback_voice_used']).lower()}`",
        f"- Turn count: `{len(packet['turns'])}`",
        "",
        "This is a supervised live voice acceptance packet. Passing it does not mean production readiness.",
        "Failing it should produce narrow follow-up tickets, not broad runtime rewrites.",
        "The recommended spoken path and optional stress turns are sample scenarios only, not runtime caps.",
        "",
        "## Hard Gates",
        "",
    ]
    for name, gate in packet["hard_gates"].items():
        lines.append(f"- `{name}`: `{str(gate.get('passed')).lower()}`")
    lines.extend(["", "## Human Gates", ""])
    for name, value in packet["human_quality_gates"].items():
        lines.append(f"- `{name}`: `{value}`")
    lines.extend(["", "## Manual Review Status", ""])
    if result["status"] == "pending_manual_review":
        lines.append("- Manual review is incomplete. Fill `manual_review` for every turn before accepting this checkpoint.")
    else:
        lines.append(f"- Human failures: `{', '.join(result['human_gate_failures']) or 'none'}`")
        lines.append(f"- Hard failures: `{', '.join(result['hard_gate_failures']) or 'none'}`")
    lines.extend(["", "## Recommended Spoken Test Path", ""])
    for item in packet["recommended_spoken_test_path"]:
        lines.append(f"- {item['step']}. {item['speaker']}: {item['prompt']} ({item['purpose']})")
    lines.extend(["", "## Optional Stress Turns", ""])
    lines.extend(f"- {turn}" for turn in packet["optional_stress_turns"])
    lines.extend(["", "## Next Recommendation", "", f"- {result['recommendation']}"])
    return "\n".join(lines)


def render_review_form(packet: dict[str, Any], csv_path: Path | None = None) -> str:
    lines = [
        "# LIVE-DEMO-003 Manual Review Form",
        "",
        "Use this file to review the live call. The JSON packet is the machine artifact; this form explains the fields in plain language.",
        "For machine evaluation, fill the companion CSV and rerun the generator with `--manual-review-csv`.",
        "",
        f"- Checkpoint: `{packet['checkpoint_id']}`",
        f"- Demo session: `{packet['demo_session_id']}`",
        f"- Campaign: `{packet['campaign_id']}`",
        f"- Provider TTS used: `{str(packet['provider_tts_used']).lower()}`",
        f"- Browser fallback voice used: `{str(packet['browser_fallback_voice_used']).lower()}`",
    ]
    if csv_path:
        lines.append(f"- Review CSV: `{csv_path}`")
    lines.extend(["", "## Field Guide", ""])
    for field in MANUAL_REVIEW_FIELDS:
        lines.append(f"- `{field}`: {MANUAL_REVIEW_FIELD_HELP[field]}")
    lines.extend(["", "## Turn Review", ""])
    for turn in packet.get("turns", []):
        transcript = str(turn.get("transcript") or "").replace("\n", " ").strip()
        response = str(turn.get("final_response") or "").replace("\n", " ").strip()
        lines.extend(
            [
                f"### Turn {turn.get('turn_index')}",
                "",
                f"- You said: {transcript}",
                f"- Agent said: {response}",
                f"- Call control: `{turn.get('call_control')}`",
                "",
                "Fill in the CSV row for this turn. Use 1-5 scores, true/false booleans, and short notes.",
                "",
            ]
        )
    return "\n".join(lines)


def write_manual_review_csv(path: Path, packet: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["turn_index", "transcript", "final_response", *MANUAL_REVIEW_FIELDS]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for turn in packet.get("turns", []):
            review = turn.get("manual_review") or {}
            writer.writerow(
                {
                    "turn_index": turn.get("turn_index"),
                    "transcript": str(turn.get("transcript") or "").replace("\n", " "),
                    "final_response": str(turn.get("final_response") or "").replace("\n", " "),
                    **{field: review.get(field) if review.get(field) is not None else "" for field in MANUAL_REVIEW_FIELDS},
                }
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate or evaluate LIVE-DEMO-003 supervised live voice acceptance packets.")
    parser.add_argument("--out", default=str(DEFAULT_PACKET_OUT))
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT_OUT))
    parser.add_argument("--review-form-out", default=str(DEFAULT_REVIEW_FORM_OUT))
    parser.add_argument("--review-csv-out", default=str(DEFAULT_REVIEW_CSV_OUT))
    parser.add_argument("--manual-review-csv", help="CSV with filled manual review fields to apply before evaluation.")
    parser.add_argument("--input", help="Existing acceptance packet to evaluate and report.")
    parser.add_argument("--from-private-turns", help="Explicitly read private LIVE-DEMO-001 turn JSON files from this directory.")
    parser.add_argument("--session-id", default="LIVE-DEMO-003-synthetic-sample")
    parser.add_argument("--campaign", default=DEFAULT_CAMPAIGN_ID)
    parser.add_argument("--stage", default=DEFAULT_STAGE)
    parser.add_argument("--cases", default=str(DEFAULT_CASES_PATH))
    parser.add_argument("--private-out", default=str(DEFAULT_PRIVATE_OUT))
    parser.add_argument("--timeout-seconds", type=float, default=8.0)
    parser.add_argument("--live-tts", action="store_true", help="Explicitly allow live TTS while building synthetic acceptance turns.")
    parser.add_argument("--force-key-missing", action="store_true")
    parser.add_argument("--consent-confirmed", action="store_true")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.live_tts and not args.consent_confirmed:
        raise SystemExit("--consent-confirmed is required with --live-tts.")
    if args.timeout_seconds <= 0 or args.timeout_seconds > 10:
        raise SystemExit("--timeout-seconds must be greater than 0 and no more than 10.")

    if args.input:
        packet = json.loads(Path(args.input).read_text(encoding="utf-8"))
        packet["hard_gates"] = hard_gate_results(list(packet.get("turns") or []))
        packet["human_quality_gates"] = human_quality_gate_defaults()
        packet["acceptance_result"] = evaluate_acceptance(packet)
    elif args.from_private_turns:
        session_id = None if args.session_id == "LIVE-DEMO-003-synthetic-sample" else args.session_id
        turns = load_private_turns(Path(args.from_private_turns).resolve(), session_id)
        if not turns:
            raise SystemExit("No matching LIVE-DEMO-001 private turn JSON files found.")
        packet = build_packet(turns, args)
    else:
        packet = build_packet(build_synthetic_turns(args), args)

    if args.manual_review_csv:
        apply_manual_review_csv(packet, Path(args.manual_review_csv).resolve())
    packet["hard_gates"] = hard_gate_results(list(packet.get("turns") or []))
    packet["human_quality_gates"] = human_quality_gate_defaults()
    packet["acceptance_result"] = evaluate_acceptance(packet)

    out = Path(args.out).resolve()
    report_out = Path(args.report_out).resolve()
    review_form_out = Path(args.review_form_out).resolve()
    review_csv_out = Path(args.review_csv_out).resolve()
    write_json(out, packet)
    write_text(report_out, render_report(packet))
    write_text(review_form_out, render_review_form(packet, review_csv_out))
    manual_review_csv = Path(args.manual_review_csv).resolve() if args.manual_review_csv else None
    if manual_review_csv is None or manual_review_csv != review_csv_out:
        write_manual_review_csv(review_csv_out, packet)
    print(
        json.dumps(
            {
                "packet": str(out),
                "report": str(report_out),
                "review_form": str(review_form_out),
                "review_csv": str(review_csv_out),
                "status": packet["acceptance_result"]["status"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
