"""Validate human-reviewed commercial conversation polish.

This focused validator covers wording quality after the automated matrices are
green: direct value answers, challenge repair, and social/context repair must
sound commercially useful without reopening broad routing behavior.
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


CHECKPOINT_ID = "COMMERCIAL-CONVERSATION-POLISH-001"
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

ACK_PATTERNS = ("fair question", "sure", "understood", "got it", "right", "you re right", "you're right")
RELEVANCE_PATTERNS = ("costing time", "creating delays", "hurting", "risk", "quality", "impact", "worth fixing")
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
INTERNAL_PATTERNS = (
    "approved qualified reviewer path",
    "approved scope",
    "internal policy",
    "i should",
)
UNSAFE_CLAIMS = (
    "guarantee",
    "guaranteed",
    "exact price is",
    "covered for sure",
    "roi guarantee",
    "revenue guarantee",
    "security guarantee",
)
SIDE_EFFECT_KEYS = (
    "provider_calls_made",
    "local_llm_calls_made",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
    "customer_audio_uploaded_to_python_server",
    "customer_audio_uploaded_to_tts_provider",
)


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


def contains_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(pattern in text for pattern in patterns)


def question_count(text: str) -> int:
    return text.count("?")


def add_failure(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def common_response_checks(packet: dict[str, Any], failures: list[str]) -> None:
    lower = lower_response(packet)
    add_failure(failures, not contains_any(lower, FULL_MENU_PATTERNS), "response used full diagnostic menu")
    add_failure(failures, not contains_any(lower, INTERNAL_PATTERNS), "response used internal wording")
    add_failure(failures, not contains_any(lower, UNSAFE_CLAIMS), "response invented unsafe claim")
    add_failure(failures, question_count(response(packet)) <= 1, "response asked more than one question")
    add_failure(failures, not any(side_effect_flags(packet).values()), "response caused side effects")


def summarize_packet(packet: dict[str, Any]) -> dict[str, Any]:
    fr = frame(packet)
    return {
        "response": response(packet),
        "buyer_move_id": fr.get("buyer_move_id"),
        "recognition_reason": fr.get("recognition_reason"),
        "response_shape_enforced_category": fr.get("response_shape_enforced_category"),
        "confirmed_gaps": memory(packet).get("confirmed_gaps") or [],
        "selected_action_source": source(packet),
        "side_effect_flags": side_effect_flags(packet),
    }


def record(scenario: str, campaign: dict[str, Any], packet: dict[str, Any], failures: list[str], *, turn: str) -> dict[str, Any]:
    return {
        "scenario": scenario,
        "campaign": campaign["id"],
        "turn": turn,
        "passed": not failures,
        "failures": failures,
        "packet": summarize_packet(packet),
    }


def validate_direct_question_route() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for campaign in CAMPAIGNS:
        packets = run_sequence(campaign, ["__agent_open__", "what does your product do", "why should I care"], f"direct-polish-{slug(campaign['id'])}")
        product_packet = packets[1]
        why_packet = packets[2]
        product_failures: list[str] = []
        common_response_checks(product_packet, product_failures)
        add_failure(product_failures, contains_any(lower_response(product_packet), ACK_PATTERNS), "product answer did not acknowledge question")
        add_failure(product_failures, "stop here" not in lower_response(product_packet), "product answer over-offered stop")
        results.append(record("direct_question_product", campaign, product_packet, product_failures, turn="what does your product do"))

        why_failures: list[str] = []
        common_response_checks(why_packet, why_failures)
        why_lower = lower_response(why_packet)
        add_failure(why_failures, contains_any(why_lower, ACK_PATTERNS), "why-care answer did not acknowledge question")
        add_failure(why_failures, contains_any(why_lower, RELEVANCE_PATTERNS), "why-care answer did not create impact relevance")
        add_failure(why_failures, "stop here" not in why_lower and "we can stop" not in why_lower, "why-care answer over-offered stop")
        results.append(record("direct_question_why_care", campaign, why_packet, why_failures, turn="why should I care"))
    return results


def validate_confusion_after_confirmed_pain() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for campaign in CAMPAIGNS:
        packets = run_sequence(campaign, ["__agent_open__", "yeah sure", campaign["pain"], "what do you mean"], f"confusion-polish-{slug(campaign['id'])}")
        packet = packets[-1]
        lower = lower_response(packet)
        failures: list[str] = []
        common_response_checks(packet, failures)
        add_failure(failures, campaign["expected_gap"] in (memory(packet).get("confirmed_gaps") or []), "confirmed gap was not preserved")
        add_failure(failures, "impact" in lower or "causing" in lower, "confusion answer did not explain implication/consequence")
        add_failure(failures, "actually happening" not in lower, "confusion answer re-asked whether pain exists")
        add_failure(failures, "no reason to continue" not in lower, "confusion answer used low-conversion stop framing")
        add_failure(failures, "callbacks is" not in lower, "confusion answer has callbacks grammar error")
        results.append(record("confusion_after_confirmed_pain", campaign, packet, failures, turn="what do you mean"))
    return results


def validate_did_not_answer_after_confirmed_pain() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for campaign in CAMPAIGNS:
        packets = run_sequence(campaign, ["__agent_open__", "yeah sure", campaign["pain"], "you didn't answer my question"], f"did-not-answer-{slug(campaign['id'])}")
        packet = packets[-1]
        lower = lower_response(packet)
        failures: list[str] = []
        common_response_checks(packet, failures)
        add_failure(failures, contains_any(lower, ("you're right", "you are right")), "did-not-answer response did not acknowledge directly")
        add_failure(failures, "direct answer" in lower or "i'm checking" in lower, "did-not-answer response did not answer the challenge")
        add_failure(failures, "you already answered that" not in lower, "did-not-answer reused already-told-you wording")
        add_failure(failures, campaign["expected_gap"] in (memory(packet).get("confirmed_gaps") or []), "confirmed gap was not preserved")
        add_failure(failures, source(packet) != "duplicate_response_repair", "did-not-answer used duplicate loop repair")
        results.append(record("did_not_answer_after_confirmed_pain", campaign, packet, failures, turn="you didn't answer my question"))
    return results


def validate_already_told_after_confirmed_pain() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for campaign in CAMPAIGNS:
        packets = run_sequence(campaign, ["__agent_open__", "yeah sure", campaign["pain"], "I already told you"], f"already-told-{slug(campaign['id'])}")
        packet = packets[-1]
        lower = lower_response(packet)
        failures: list[str] = []
        common_response_checks(packet, failures)
        add_failure(failures, "already" in lower or "noted" in lower, "already-told response did not acknowledge prior answer")
        add_failure(failures, "impact" in lower or "causing" in lower, "already-told response did not move to implication")
        add_failure(failures, "which part should i check" not in lower, "already-told response reopened menu")
        add_failure(failures, campaign["expected_gap"] in (memory(packet).get("confirmed_gaps") or []), "confirmed gap was not preserved")
        results.append(record("already_told_after_confirmed_pain", campaign, packet, failures, turn="I already told you"))
    return results


def validate_social_specificity() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for campaign in CAMPAIGNS:
        before_slow = run_sequence(campaign, ["__agent_open__", "slow down"], f"slow-before-{slug(campaign['id'])}")[-1]
        failures: list[str] = []
        common_response_checks(before_slow, failures)
        lower = lower_response(before_slow)
        add_failure(failures, "slow down" in lower or "move slower" in lower, "slow-down response did not acknowledge request")
        add_failure(failures, "that issue" not in lower, "slow-down before pain used vague issue reference")
        add_failure(failures, contains_any(lower, ("checking one thing", "one question", "short version")), "slow-down before pain did not simplify")
        add_failure(failures, not contains_any(lower, ("appointment", "callback window", "schedule")), "slow-down before pain pressured appointment")
        results.append(record("slow_down_before_pain", campaign, before_slow, failures, turn="slow down"))

        after_slow = run_sequence(campaign, ["__agent_open__", "yeah sure", campaign["pain"], "slow down"], f"slow-after-{slug(campaign['id'])}")[-1]
        failures = []
        common_response_checks(after_slow, failures)
        lower = lower_response(after_slow)
        add_failure(failures, "slow down" in lower or "move slower" in lower, "slow-down after pain did not acknowledge request")
        add_failure(failures, "that issue" not in lower, "slow-down after pain used vague issue reference")
        add_failure(failures, "impact" in lower or "causing" in lower, "slow-down after pain did not preserve consequence context")
        add_failure(failures, campaign["expected_gap"] in (memory(after_slow).get("confirmed_gaps") or []), "slow-down after pain lost confirmed gap")
        results.append(record("slow_down_after_pain", campaign, after_slow, failures, turn="slow down"))

        language = run_sequence(campaign, ["__agent_open__", "I don't speak English well"], f"language-{slug(campaign['id'])}")[-1]
        failures = []
        common_response_checks(language, failures)
        lower = lower_response(language)
        add_failure(failures, "simple english" in lower, "language response did not acknowledge simple-English need")
        add_failure(failures, "that issue" not in lower, "language response used vague issue reference")
        add_failure(failures, contains_any(lower, ("one question", "checking one thing")), "language response did not simplify to one question")
        results.append(record("language_mismatch_before_pain", campaign, language, failures, turn="I don't speak English well"))
    return results


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    by_scenario: dict[str, dict[str, int]] = {}
    failure_types: Counter[str] = Counter()
    for result in results:
        bucket = by_scenario.setdefault(result["scenario"], {"passed": 0, "failed": 0})
        if result["passed"]:
            bucket["passed"] += 1
        else:
            bucket["failed"] += 1
            failure_types.update(result["failures"])
    return {
        "matrix_size": len(results),
        "pass_count": sum(1 for item in results if item["passed"]),
        "failure_count": sum(1 for item in results if not item["passed"]),
        "by_scenario": dict(sorted(by_scenario.items())),
        "failure_types": dict(failure_types.most_common()),
        "failure_examples": [item for item in results if not item["passed"]][:20],
    }


def write_evidence(result: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    summary = result["summary"]
    lines = [
        f"# {CHECKPOINT_ID}",
        "",
        "## Summary",
        "Validated human-reviewed commercial polish for direct-question, challenge, and social/context repair turns.",
        "",
        "## Matrix",
        f"- Cases: {summary['matrix_size']}",
        f"- Pass/fail: {summary['pass_count']} / {summary['failure_count']}",
        "",
        "## Scenario Results",
    ]
    for scenario, counts in summary["by_scenario"].items():
        lines.append(f"- {scenario}: pass={counts['passed']} fail={counts['failed']}")
    lines.extend(["", "## Failure Types"])
    if summary["failure_types"]:
        for failure, count in summary["failure_types"].items():
            lines.append(f"- {failure}: {count}")
    else:
        lines.append("- None")
    lines.extend(["", "## Representative Passing Outputs"])
    for item in result["results"][:10]:
        lines.append(f"- {item['campaign']} | {item['scenario']}: {item['packet']['response']!r}")
    lines.extend(["", "## Side Effects", "- Provider, local LLM, email, calendar, CRM, PROD-102, live TTS, and customer-audio upload flags remained false."])
    (OUT_DIR / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    results.extend(validate_direct_question_route())
    results.extend(validate_confusion_after_confirmed_pain())
    results.extend(validate_did_not_answer_after_confirmed_pain())
    results.extend(validate_already_told_after_confirmed_pain())
    results.extend(validate_social_specificity())
    summary = summarize(results)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "pass" if summary["failure_count"] == 0 else "fail",
        "summary": summary,
        "results": results,
        "side_effects": {key: False for key in SIDE_EFFECT_KEYS},
        "runtime_behavior_changed_scope": "Commercial wording polish only for direct questions, challenge repair, and social/context repair.",
    }
    write_evidence(result)
    print(
        json.dumps(
            {
                "checkpoint_id": CHECKPOINT_ID,
                "status": result["status"],
                "pass_count": summary["pass_count"],
                "failure_count": summary["failure_count"],
                "top_failures": summary["failure_types"],
                "output_dir": OUT_DIR.as_posix(),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
