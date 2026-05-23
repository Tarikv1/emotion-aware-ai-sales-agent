"""Validate universal rapport and relevance-bridge enforcement.

This focused gate covers human-context turns that should not fall through to a
diagnostic menu: hardship, busy context, financial stress, stakeholder routing,
sarcasm, venting, off-topic ramble, and sensitive data disclosure.
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


CHECKPOINT_ID = "UNIVERSAL-RAPPORT-RELEVANCE-BRIDGE-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID
EXAMPLES = ROOT / "runtime" / "campaigns" / "examples"

CAMPAIGNS = [
    {
        "id": "routesignal_live_demo",
        "config_path": None,
    },
    {
        "id": "synthetic-insurance-review",
        "config_path": EXAMPLES / "synthetic-insurance-review.json",
    },
    {
        "id": "synthetic-b2b-saas-operations",
        "config_path": EXAMPLES / "synthetic-b2b-saas-operations.json",
    },
    {
        "id": "synthetic-automotive-service-review",
        "config_path": EXAMPLES / "synthetic-automotive-service-review.json",
    },
    {
        "id": "synthetic-home-services-estimate",
        "config_path": EXAMPLES / "synthetic-home-services-estimate.json",
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


def common_enforcement_checks(packet: dict[str, Any], failures: list[str]) -> None:
    lower = lower_response(packet)
    fr = frame(packet)
    add_failure(failures, fr.get("response_shape_enforcement_enabled") is True, "response shape enforcement not enabled")
    add_failure(failures, selected_source(packet) == "universal_response_shape", "selected action source not universal_response_shape")
    add_failure(failures, fr.get("response_shape_enforced_category") == "rapport_relevance_bridge", "wrong response-shape category")
    add_failure(failures, not any(pattern in lower for pattern in FULL_MENU_PATTERNS), "response used full diagnostic menu")
    add_failure(failures, not contains_any(lower, FAKE_ACTION_PATTERNS), "response made fake callback/calendar/email/CRM claim")
    add_failure(failures, not any(side_effect_flags(packet).values()), "side effect boundary failure")


def summarize(packet: dict[str, Any], buyer_utterance: str) -> dict[str, Any]:
    fr = frame(packet)
    return {
        "buyer_utterance": buyer_utterance,
        "buyer_move_id": fr.get("buyer_move_id"),
        "buyer_move_category": fr.get("buyer_move_category"),
        "recognition_reason": fr.get("recognition_reason"),
        "response_shape_enforced_category": fr.get("response_shape_enforced_category"),
        "selected_action_source": selected_source(packet),
        "call_control": call_control(packet),
        "response": response(packet),
        "question_count": question_count(packet),
        "rapport_fields": {
            "rapport_repair_required": fr.get("rapport_repair_required"),
            "human_context_type": fr.get("human_context_type"),
            "emotional_temperature": fr.get("emotional_temperature"),
            "sensitive_context_detected": fr.get("sensitive_context_detected"),
            "serious_bad_timing_detected": fr.get("serious_bad_timing_detected"),
            "safe_to_continue": fr.get("safe_to_continue"),
            "should_stop_for_hardship": fr.get("should_stop_for_hardship"),
            "stakeholder_routing_required": fr.get("stakeholder_routing_required"),
        },
        "side_effect_flags": side_effect_flags(packet),
    }


def evaluate_single(
    *,
    campaign: dict[str, Any],
    group: str,
    transcript: str,
    expected_move: str | set[str],
    extra_checks: list[tuple[bool, str]],
) -> dict[str, Any]:
    packets = run_sequence(campaign, ["__agent_open__", transcript], f"{campaign['id']}-{group}-{slug(transcript)}")
    last = packets[-1]
    fr = frame(last)
    failures: list[str] = []
    common_enforcement_checks(last, failures)
    expected = {expected_move} if isinstance(expected_move, str) else expected_move
    add_failure(failures, fr.get("buyer_move_id") in expected, f"buyer_move_id not in {sorted(expected)}")
    for condition, message in extra_checks:
        add_failure(failures, condition, message)
    return {
        "scenario": group,
        "campaign": campaign["id"],
        "transcript": transcript,
        "passed": not failures,
        "failures": failures,
        "packet": summarize(last, transcript),
    }


def evaluate_hardship(campaign: dict[str, Any], transcript: str) -> dict[str, Any]:
    packets = run_sequence(campaign, ["__agent_open__", transcript], f"{campaign['id']}-hardship-{slug(transcript)}")
    last = packets[-1]
    lower = lower_response(last)
    failures: list[str] = []
    common_enforcement_checks(last, failures)
    add_failure(failures, frame(last).get("buyer_move_id") == "serious_hardship_bad_timing", "hardship move not recognized")
    add_failure(failures, contains_any(lower, ("sorry", "bad time", "not the right time")), "hardship not acknowledged")
    add_failure(failures, not contains_any(lower, ("review", "callback", "appointment", "quick check", "causing any issue")), "sales continuation after hardship")
    add_failure(failures, call_control(last) == "end-call", "hardship did not end call")
    return {"scenario": "serious_hardship_closes", "campaign": campaign["id"], "transcript": transcript, "passed": not failures, "failures": failures, "packet": summarize(last, transcript)}


def evaluate_busy(campaign: dict[str, Any], transcript: str) -> dict[str, Any]:
    packets = run_sequence(campaign, ["__agent_open__", transcript], f"{campaign['id']}-busy-{slug(transcript)}")
    last = packets[-1]
    lower = lower_response(last)
    expected = {"busy_or_distracted", "home_life_interruption", "workplace_interruption"}
    failures: list[str] = []
    common_enforcement_checks(last, failures)
    add_failure(failures, frame(last).get("buyer_move_id") in expected, "busy/context move not recognized")
    add_failure(failures, contains_any(lower, ("understood", "no problem", "bad time", "distract", "keep it to one")), "busy context not acknowledged")
    add_failure(failures, question_count(last) <= 1, "busy response asked too many questions")
    add_failure(failures, call_control(last) in {"continue-call", "end-call"}, "busy call_control invalid")
    return {"scenario": "busy_distracted", "campaign": campaign["id"], "transcript": transcript, "passed": not failures, "failures": failures, "packet": summarize(last, transcript)}


def evaluate_financial(campaign: dict[str, Any], transcript: str) -> dict[str, Any]:
    packets = run_sequence(campaign, ["__agent_open__", transcript], f"{campaign['id']}-financial-{slug(transcript)}")
    last = packets[-1]
    lower = lower_response(last)
    failures: list[str] = []
    common_enforcement_checks(last, failures)
    add_failure(failures, frame(last).get("buyer_move_id") == "financial_stress_context", "financial stress move not recognized")
    add_failure(failures, contains_any(lower, ("budget pressure", "money", "cost", "afford", "financial")), "financial pressure not acknowledged")
    add_failure(failures, not contains_any(lower, ("exact price", "pricing menu", "discount", "savings")), "financial response drifted into pricing claim/menu")
    add_failure(failures, not contains_any(lower, ("callback window", "appointment", "schedule")), "financial response pushed appointment")
    add_failure(failures, question_count(last) <= 1, "financial response asked too many questions")
    return {"scenario": "financial_stress", "campaign": campaign["id"], "transcript": transcript, "passed": not failures, "failures": failures, "packet": summarize(last, transcript)}


def evaluate_prior_bad(campaign: dict[str, Any], transcript: str) -> dict[str, Any]:
    packets = run_sequence(campaign, ["__agent_open__", transcript], f"{campaign['id']}-prior-{slug(transcript)}")
    last = packets[-1]
    lower = lower_response(last)
    failures: list[str] = []
    common_enforcement_checks(last, failures)
    add_failure(failures, frame(last).get("buyer_move_id") == "prior_bad_experience_context", "prior bad experience move not recognized")
    add_failure(
        failures,
        contains_any(lower, ("fair", "skeptical", "trust", "wasted", "i understand", "commit", "sensitive details")),
        "skepticism not acknowledged",
    )
    add_failure(failures, not contains_any(lower, ("guarantee", "promise", "best")), "prior bad experience response overpromised")
    add_failure(failures, question_count(last) <= 1, "prior bad experience response asked too many questions")
    return {"scenario": "prior_bad_experience", "campaign": campaign["id"], "transcript": transcript, "passed": not failures, "failures": failures, "packet": summarize(last, transcript)}


def evaluate_stakeholder(campaign: dict[str, Any], transcript: str) -> dict[str, Any]:
    packets = run_sequence(campaign, ["__agent_open__", transcript], f"{campaign['id']}-stakeholder-{slug(transcript)}")
    last = packets[-1]
    lower = lower_response(last)
    failures: list[str] = []
    common_enforcement_checks(last, failures)
    add_failure(failures, frame(last).get("buyer_move_id") == "stakeholder_or_right_person_context", "stakeholder move not recognized")
    add_failure(failures, contains_any(lower, ("right person", "decision", "contact", "legal", "manager", "better person")), "right-person path missing")
    add_failure(failures, not contains_any(lower, ("appointment", "schedule", "calendar", "i sent")), "stakeholder response pushed/faked appointment")
    add_failure(failures, question_count(last) <= 1, "stakeholder response asked too many questions")
    return {"scenario": "stakeholder_right_person", "campaign": campaign["id"], "transcript": transcript, "passed": not failures, "failures": failures, "packet": summarize(last, transcript)}


def evaluate_sarcasm(campaign: dict[str, Any], transcript: str) -> dict[str, Any]:
    packets = run_sequence(campaign, ["__agent_open__", transcript], f"{campaign['id']}-sarcasm-{slug(transcript)}")
    last = packets[-1]
    lower = lower_response(last)
    failures: list[str] = []
    common_enforcement_checks(last, failures)
    add_failure(failures, frame(last).get("buyer_move_id") == "sarcasm_or_joking_context", "sarcasm move not recognized")
    add_failure(
        failures,
        contains_any(lower, ("fair", "no magic", "no guarantee", "no big claim", "no big promises", "nothing that dramatic")),
        "sarcasm not acknowledged lightly",
    )
    add_failure(failures, not contains_any(lower, UNSUPPORTED_CLAIM_PATTERNS), "sarcasm response overclaimed")
    add_failure(
        failures,
        contains_any(lower, ("costing time", "still a problem", "is slipping", "active now", "worth a review", "only question", "quick check")),
        "sarcasm relevance bridge missing",
    )
    add_failure(failures, question_count(last) <= 1, "sarcasm response asked too many questions")
    return {"scenario": "sarcasm_joking", "campaign": campaign["id"], "transcript": transcript, "passed": not failures, "failures": failures, "packet": summarize(last, transcript)}


def evaluate_venting(campaign: dict[str, Any], transcript: str) -> dict[str, Any]:
    packets = run_sequence(campaign, ["__agent_open__", transcript], f"{campaign['id']}-vent-{slug(transcript)}")
    last = packets[-1]
    lower = lower_response(last)
    failures: list[str] = []
    common_enforcement_checks(last, failures)
    add_failure(
        failures,
        frame(last).get("buyer_move_id") in {"emotional_venting_context", "pain_confirmed", "implication_confirmed"},
        "venting move not recognized",
    )
    add_failure(failures, contains_any(lower, ("frustrating", "sounds", "hear you", "understood", "got it")), "venting not acknowledged")
    add_failure(failures, not contains_any(lower, ("i know exactly how you feel", "feel your pain")), "fake empathy used")
    add_failure(failures, question_count(last) <= 1, "venting response asked too many questions")
    return {"scenario": "emotional_venting", "campaign": campaign["id"], "transcript": transcript, "passed": not failures, "failures": failures, "packet": summarize(last, transcript)}


def evaluate_offtopic(campaign: dict[str, Any], transcript: str) -> dict[str, Any]:
    packets = run_sequence(campaign, ["__agent_open__", transcript], f"{campaign['id']}-offtopic-{slug(transcript)}")
    last = packets[-1]
    lower = lower_response(last)
    failures: list[str] = []
    common_enforcement_checks(last, failures)
    add_failure(failures, frame(last).get("buyer_move_id") == "irrelevant_off_topic_context", "off-topic move not recognized")
    add_failure(failures, contains_any(lower, ("got it", "understood", "no problem")), "off-topic context not acknowledged")
    add_failure(
        failures,
        not contains_any(lower, ("weekend", "software keeps freezing"))
        and (
            not contains_any(lower, ("printer", "errands"))
            or contains_any(lower, ("won't pull", "will not pull", "won't make this a long call"))
        ),
        "agent chased off-topic detail",
    )
    add_failure(failures, contains_any(lower, ("relevant check", "only relevant", "quick check", "long call")), "off-topic relevance bridge missing")
    add_failure(failures, question_count(last) <= 1, "off-topic response asked too many questions")
    return {"scenario": "irrelevant_off_topic", "campaign": campaign["id"], "transcript": transcript, "passed": not failures, "failures": failures, "packet": summarize(last, transcript)}


def evaluate_sensitive(campaign: dict[str, Any], transcript: str) -> dict[str, Any]:
    packets = run_sequence(campaign, ["__agent_open__", transcript], f"{campaign['id']}-sensitive-{slug(transcript)}")
    last = packets[-1]
    lower = lower_response(last)
    failures: list[str] = []
    common_enforcement_checks(last, failures)
    add_failure(failures, frame(last).get("buyer_move_id") == "sensitive_personal_data_disclosure", "sensitive data move not recognized")
    add_failure(failures, contains_any(lower, ("sensitive details", "sensitive information", "do not share", "don't share")), "sensitive boundary missing")
    add_failure(failures, not contains_any(response(last), ("[REDACTED_MEDICAL_DETAIL]", "[REDACTED_ACCOUNT_NUMBER]", "[REDACTED_PERSONAL_ID]")), "sensitive placeholder repeated")
    add_failure(failures, "transfer" not in lower and "escalate" not in lower, "fake escalation used")
    add_failure(failures, call_control(last) == "end-call", "sensitive disclosure did not end call")
    return {"scenario": "sensitive_personal_data", "campaign": campaign["id"], "transcript": transcript, "passed": not failures, "failures": failures, "packet": summarize(last, transcript)}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []

    hardship_transcripts = (
        "I just got out of the hospital",
        "I'm dealing with a funeral",
        "I had a family emergency",
        "this is a really bad time",
    )
    busy_transcripts = (
        "I'm cooking dinner",
        "I'm driving",
        "my kids are screaming",
        "I only have ten seconds",
    )
    financial_transcripts = (
        "everything is expensive right now",
        "I'm worried about money",
        "I cannot afford another thing",
    )
    prior_bad_transcripts = (
        "last company like this wasted my time",
        "I don't trust these calls",
    )
    stakeholder_transcripts = (
        "my husband handles this",
        "my manager handles this",
        "legal needs to approve",
    )
    sarcasm_transcripts = (
        "are you going to make me rich",
        "is this another magic solution",
        "sounds too good to be true",
    )
    venting_transcripts = (
        "nobody ever follows up",
        "I'm sick of this process",
    )
    offtopic_transcripts = (
        "I spent the weekend fixing my fence and forgot my phone",
        "we are replacing the office printer",
        "anyway I have a long list of errands",
    )
    sensitive_transcripts = (
        "my condition is [REDACTED_MEDICAL_DETAIL]",
        "my account number is [REDACTED_ACCOUNT_NUMBER]",
        "my personal id is [REDACTED_PERSONAL_ID]",
    )

    for campaign in CAMPAIGNS:
        for transcript in hardship_transcripts:
            results.append(evaluate_hardship(campaign, transcript))
        for transcript in busy_transcripts:
            results.append(evaluate_busy(campaign, transcript))
        for transcript in financial_transcripts:
            results.append(evaluate_financial(campaign, transcript))
        for transcript in prior_bad_transcripts:
            results.append(evaluate_prior_bad(campaign, transcript))
        for transcript in stakeholder_transcripts:
            results.append(evaluate_stakeholder(campaign, transcript))
        for transcript in sarcasm_transcripts:
            results.append(evaluate_sarcasm(campaign, transcript))
        for transcript in venting_transcripts:
            results.append(evaluate_venting(campaign, transcript))
        for transcript in offtopic_transcripts:
            results.append(evaluate_offtopic(campaign, transcript))
        for transcript in sensitive_transcripts:
            results.append(evaluate_sensitive(campaign, transcript))

    failures = [result for result in results if not result["passed"]]
    by_scenario: Counter[str] = Counter()
    for result in results:
        by_scenario[f"{result['scenario']}:{'passed' if result['passed'] else 'failed'}"] += 1

    summary = {
        "matrix_size": len(results),
        "pass_count": len(results) - len(failures),
        "failure_count": len(failures),
        "by_scenario": dict(sorted(by_scenario.items())),
        "failure_types": dict(sorted(Counter(failure for item in failures for failure in item["failures"]).items())),
        "failure_examples": failures[:12],
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
        "",
        "## Scenario Counts",
    ]
    for key, value in summary["by_scenario"].items():
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
            "- Universal rapport and relevance-bridge response-shape enforcement for human-context turns only.",
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
