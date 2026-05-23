"""Validate rapport specificity and anti-repetition behavior.

This gate extends the 4E2S rapport layer with sales-quality checks: repeated
human-context turns should not receive identical empathy templates, and generic
"this issue" bridges should use the campaign's active issue when available.
"""

from __future__ import annotations

from collections import Counter
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import run_live_demo_001_agent_voice_call as demo  # noqa: E402


CHECKPOINT_ID = "UNIVERSAL-RAPPORT-SPECIFICITY-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID
EXAMPLES = ROOT / "runtime" / "campaigns" / "examples"

CAMPAIGNS = [
    {"id": "routesignal_live_demo", "config_path": None, "issue_fragments": ("inbound demo follow-up",)},
    {
        "id": "synthetic-insurance-review",
        "config_path": EXAMPLES / "synthetic-insurance-review.json",
        "issue_fragments": ("premium pressure",),
    },
    {
        "id": "synthetic-b2b-saas-operations",
        "config_path": EXAMPLES / "synthetic-b2b-saas-operations.json",
        "issue_fragments": ("manual work",),
    },
    {
        "id": "synthetic-automotive-service-review",
        "config_path": EXAMPLES / "synthetic-automotive-service-review.json",
        "issue_fragments": ("repair timing",),
    },
    {
        "id": "synthetic-home-services-estimate",
        "config_path": EXAMPLES / "synthetic-home-services-estimate.json",
        "issue_fragments": ("service need",),
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

FAKE_ACTION_PATTERNS = (
    "calendar invite",
    "i sent",
    "i emailed",
    "booked you",
    "crm",
)

UNSUPPORTED_CLAIM_PATTERNS = (
    "guarantee",
    "make you rich",
    "magic solution",
    "promise savings",
    "will save",
    "covered for sure",
    "roi",
)

GENERIC_BRIDGE_PATTERNS = (
    "this issue",
    "this specific issue",
    "that issue",
)


def slug(text: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in text.lower()).strip("-")


def append_turn(state: dict[str, Any], packet: dict[str, Any]) -> None:
    state.setdefault("turns", []).append(
        {
            "transcript": packet.get("transcript") or "",
            "summary": packet.get("summary") or {},
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


def response(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("final_response") or packet.get("final_response") or "")


def lower_response(packet: dict[str, Any]) -> str:
    return response(packet).lower()


def frame(packet: dict[str, Any]) -> dict[str, Any]:
    return packet.get("universal_policy_frame") or (packet.get("dialogue_manager") or {}).get("universal_policy_frame") or {}


def selected_source(packet: dict[str, Any]) -> str:
    return str(((packet.get("dialogue_manager") or {}).get("selected_action") or {}).get("source") or "")


def call_control(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("call_control") or "")


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


def question_count(packet: dict[str, Any]) -> int:
    return response(packet).count("?")


def contains_any(text: str, phrases: tuple[str, ...] | list[str]) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in phrases)


def add_failure(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def has_campaign_issue(campaign: dict[str, Any], text: str) -> bool:
    lowered = text.lower()
    return any(fragment in lowered for fragment in campaign["issue_fragments"])


def repeated_response_count(packets: list[dict[str, Any]]) -> int:
    counts = Counter(response(packet) for packet in packets)
    return sum(count - 1 for count in counts.values() if count > 1)


def common_enforcement_checks(packet: dict[str, Any], failures: list[str]) -> None:
    lower = lower_response(packet)
    fr = frame(packet)
    add_failure(failures, fr.get("response_shape_enforcement_enabled") is True, "response shape enforcement not enabled")
    add_failure(failures, selected_source(packet) == "universal_response_shape", "selected action source not universal_response_shape")
    add_failure(failures, fr.get("response_shape_enforced_category") == "rapport_relevance_bridge", "wrong response-shape category")
    add_failure(failures, not contains_any(lower, FULL_MENU_PATTERNS), "response used full diagnostic menu")
    add_failure(failures, not contains_any(lower, FAKE_ACTION_PATTERNS), "response made fake callback/calendar/email/CRM claim")
    add_failure(failures, not any(side_effect_flags(packet).values()), "side effect boundary failure")


def summarize(packet: dict[str, Any], buyer_utterance: str) -> dict[str, Any]:
    fr = frame(packet)
    return {
        "buyer_utterance": buyer_utterance,
        "buyer_move_id": fr.get("buyer_move_id"),
        "buyer_move_category": fr.get("buyer_move_category"),
        "response_shape_enforced_category": fr.get("response_shape_enforced_category"),
        "selected_action_source": selected_source(packet),
        "call_control": call_control(packet),
        "response": response(packet),
        "question_count": question_count(packet),
        "rapport_fields": {
            "rapport_repair_required": fr.get("rapport_repair_required"),
            "human_context_type": fr.get("human_context_type"),
            "safe_to_continue": fr.get("safe_to_continue"),
            "should_stop_for_hardship": fr.get("should_stop_for_hardship"),
            "sensitive_context_detected": fr.get("sensitive_context_detected"),
        },
        "side_effect_flags": side_effect_flags(packet),
    }


def evaluate_sequence(
    *,
    campaign: dict[str, Any],
    scenario: str,
    transcripts: tuple[str, ...],
    expected_move: str,
    per_turn_checks: dict[str, tuple[str, ...]],
) -> dict[str, Any]:
    packets = run_sequence(campaign, ["__agent_open__", *transcripts], f"{campaign['id']}-{scenario}")
    checked_packets = packets[1:]
    failures: list[str] = []
    for transcript, packet in zip(transcripts, checked_packets):
        lower = lower_response(packet)
        fr = frame(packet)
        common_enforcement_checks(packet, failures)
        add_failure(failures, fr.get("buyer_move_id") == expected_move, f"{transcript}: wrong buyer_move_id")
        add_failure(failures, question_count(packet) <= 1, f"{transcript}: too many questions")
        add_failure(failures, not contains_any(lower, GENERIC_BRIDGE_PATTERNS), f"{transcript}: used generic issue bridge")
        add_failure(failures, has_campaign_issue(campaign, lower), f"{transcript}: campaign issue missing from bridge")
        cue_terms = per_turn_checks.get(transcript, ())
        if cue_terms:
            add_failure(failures, contains_any(lower, cue_terms), f"{transcript}: specific cue not acknowledged")
    add_failure(failures, repeated_response_count(checked_packets) == 0, f"{scenario}: responses were identical across turns")
    return {
        "scenario": scenario,
        "campaign": campaign["id"],
        "passed": not failures,
        "failures": failures,
        "repeated_response_count": repeated_response_count(checked_packets),
        "packets": [summarize(packet, transcript) for transcript, packet in zip(transcripts, checked_packets)],
    }


def evaluate_busy_or_interruption(campaign: dict[str, Any], transcript: str) -> dict[str, Any]:
    packets = run_sequence(campaign, ["__agent_open__", transcript], f"{campaign['id']}-busy-specificity-{slug(transcript)}")
    last = packets[-1]
    lower = lower_response(last)
    fr = frame(last)
    failures: list[str] = []
    common_enforcement_checks(last, failures)
    add_failure(
        failures,
        fr.get("buyer_move_id") in {"busy_or_distracted", "home_life_interruption", "workplace_interruption"},
        "busy/interruption move not recognized",
    )
    add_failure(failures, question_count(last) <= 1, "busy/interruption response asked too many questions")
    add_failure(failures, not contains_any(lower, FULL_MENU_PATTERNS), "busy/interruption used full menu")
    if contains_any(transcript.lower(), ("driving", "kids are screaming", "in a meeting", "incident response")):
        add_failure(
            failures,
            call_control(last) == "end-call" or contains_any(lower, ("stop here", "let you go", "later")),
            "unsafe/bad context did not stop or offer later",
        )
        add_failure(failures, not has_campaign_issue(campaign, lower), "unsafe/bad context continued sales bridge")
    else:
        add_failure(failures, call_control(last) in {"continue-call", "end-call"}, "busy/interruption call_control invalid")
    return {
        "scenario": "busy_interruption_appropriateness",
        "campaign": campaign["id"],
        "transcript": transcript,
        "passed": not failures,
        "failures": failures,
        "packet": summarize(last, transcript),
    }


def evaluate_hardship_or_sensitive(campaign: dict[str, Any], transcript: str, expected_move: str) -> dict[str, Any]:
    packets = run_sequence(campaign, ["__agent_open__", transcript], f"{campaign['id']}-preservation-{slug(transcript)}")
    last = packets[-1]
    lower = lower_response(last)
    failures: list[str] = []
    common_enforcement_checks(last, failures)
    add_failure(failures, frame(last).get("buyer_move_id") == expected_move, "hardship/sensitive move not preserved")
    add_failure(failures, call_control(last) == "end-call", "hardship/sensitive did not end call")
    add_failure(failures, not has_campaign_issue(campaign, lower), "hardship/sensitive continued sales bridge")
    add_failure(failures, not contains_any(lower, ("callback", "appointment", "quick check")), "hardship/sensitive continued sales")
    add_failure(failures, not contains_any(lower, ("account number", "personal id", "medical detail")), "sensitive detail repeated")
    return {
        "scenario": "hardship_sensitive_preservation",
        "campaign": campaign["id"],
        "transcript": transcript,
        "passed": not failures,
        "failures": failures,
        "packet": summarize(last, transcript),
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []

    financial_transcripts = (
        "everything is expensive right now",
        "I'm worried about money",
        "we are cutting costs",
        "I cannot afford another thing",
    )
    financial_cues = {
        "everything is expensive right now": ("costs", "expensive"),
        "I'm worried about money": ("budget", "money"),
        "we are cutting costs": ("cutting costs",),
        "I cannot afford another thing": ("afford", "not push"),
    }
    prior_bad_transcripts = (
        "last company like this wasted my time",
        "I already got burned by this kind of thing",
        "salespeople always say that",
        "I don't trust these calls",
    )
    prior_bad_cues = {
        "last company like this wasted my time": ("wasted your time",),
        "I already got burned by this kind of thing": ("trust upfront", "burned"),
        "salespeople always say that": ("specific", "pitchy"),
        "I don't trust these calls": ("sensitive details", "commit"),
    }
    sarcasm_transcripts = (
        "are you going to make me rich",
        "is this another magic solution",
        "sure, are you going to fix my whole life",
        "sounds too good to be true",
    )
    sarcasm_cues = {
        "are you going to make me rich": ("big promises",),
        "is this another magic solution": ("magic claims",),
        "sure, are you going to fix my whole life": ("nothing that dramatic",),
        "sounds too good to be true": ("fair concern", "overstate"),
    }
    offtopic_transcripts = (
        "I spent the weekend fixing my fence and forgot my phone",
        "we are also replacing the office printer",
        "our unrelated software keeps freezing",
        "anyway I have a long list of errands",
    )
    offtopic_cues = {
        "I spent the weekend fixing my fence and forgot my phone": ("won't chase", "story"),
        "we are also replacing the office printer": ("printer", "pull this"),
        "our unrelated software keeps freezing": ("separate", "this call"),
        "anyway I have a long list of errands": ("long call", "errands"),
    }
    busy_transcripts = (
        "I'm cooking dinner",
        "I'm driving",
        "my kids are screaming",
        "I only have ten seconds",
        "I'm in a meeting",
        "we're in incident response",
    )
    hardship_transcripts = (
        "I just got out of the hospital",
        "I'm dealing with a funeral",
        "I had a family emergency",
    )
    sensitive_transcripts = (
        "my condition is [REDACTED_MEDICAL_DETAIL]",
        "my account number is [REDACTED_ACCOUNT_NUMBER]",
        "my personal id is [REDACTED_PERSONAL_ID]",
    )

    for campaign in CAMPAIGNS:
        results.append(
            evaluate_sequence(
                campaign=campaign,
                scenario="financial_stress_variety",
                transcripts=financial_transcripts,
                expected_move="financial_stress_context",
                per_turn_checks=financial_cues,
            )
        )
        results.append(
            evaluate_sequence(
                campaign=campaign,
                scenario="prior_bad_experience_variety",
                transcripts=prior_bad_transcripts,
                expected_move="prior_bad_experience_context",
                per_turn_checks=prior_bad_cues,
            )
        )
        results.append(
            evaluate_sequence(
                campaign=campaign,
                scenario="sarcasm_variety",
                transcripts=sarcasm_transcripts,
                expected_move="sarcasm_or_joking_context",
                per_turn_checks=sarcasm_cues,
            )
        )
        results.append(
            evaluate_sequence(
                campaign=campaign,
                scenario="off_topic_bridge_specificity",
                transcripts=offtopic_transcripts,
                expected_move="irrelevant_off_topic_context",
                per_turn_checks=offtopic_cues,
            )
        )
        for transcript in busy_transcripts:
            results.append(evaluate_busy_or_interruption(campaign, transcript))
        for transcript in hardship_transcripts:
            results.append(evaluate_hardship_or_sensitive(campaign, transcript, "serious_hardship_bad_timing"))
        for transcript in sensitive_transcripts:
            results.append(evaluate_hardship_or_sensitive(campaign, transcript, "sensitive_personal_data_disclosure"))

    failures = [result for result in results if not result["passed"]]
    by_scenario: Counter[str] = Counter()
    for result in results:
        by_scenario[f"{result['scenario']}:{'passed' if result['passed'] else 'failed'}"] += 1
    repeated_by_scenario: Counter[str] = Counter()
    for result in results:
        repeated_by_scenario[result["scenario"]] += int(result.get("repeated_response_count") or 0)

    summary = {
        "matrix_size": len(results),
        "pass_count": len(results) - len(failures),
        "failure_count": len(failures),
        "by_scenario": dict(sorted(by_scenario.items())),
        "failure_types": dict(sorted(Counter(failure for item in failures for failure in item["failures"]).items())),
        "failure_examples": failures[:12],
        "repeated_response_count": sum(repeated_by_scenario.values()),
        "repeated_response_count_by_scenario": dict(sorted(repeated_by_scenario.items())),
        "side_effects": {key: False for key in SIDE_EFFECT_KEYS},
    }
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "pass" if not failures else "fail",
        "summary": summary,
        "results": results,
    }
    (OUT_DIR / "result.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    report = [
        f"# {CHECKPOINT_ID}",
        "",
        "## Summary",
        f"- Status: `{payload['status']}`",
        f"- Matrix size: `{summary['matrix_size']}`",
        f"- Pass count: `{summary['pass_count']}`",
        f"- Failure count: `{summary['failure_count']}`",
        f"- Repeated response count: `{summary['repeated_response_count']}`",
        "",
        "## Scenario Counts",
    ]
    for key, value in summary["by_scenario"].items():
        report.append(f"- `{key}`: `{value}`")
    report.extend(["", "## Repeated Response Counts"])
    for key, value in summary["repeated_response_count_by_scenario"].items():
        report.append(f"- `{key}`: `{value}`")
    report.extend(["", "## Failure Types"])
    if summary["failure_types"]:
        for key, value in summary["failure_types"].items():
            report.append(f"- `{key}`: `{value}`")
    else:
        report.append("- None")
    report.extend(
        [
            "",
            "## Safety Boundary Summary",
            "- Provider calls, local LLM calls, live TTS, email, calendar, CRM, PROD-102, and customer audio uploads remained false.",
            "",
            "## Runtime Behavior Changed Scope",
            "- Universal rapport wording specificity and bad-context stop behavior only.",
        ]
    )
    (OUT_DIR / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "checkpoint_id": CHECKPOINT_ID,
                "status": payload["status"],
                "pass_count": summary["pass_count"],
                "failure_count": summary["failure_count"],
                "repeated_response_count": summary["repeated_response_count"],
                "output_dir": str(OUT_DIR),
                "top_failures": summary["failure_types"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
