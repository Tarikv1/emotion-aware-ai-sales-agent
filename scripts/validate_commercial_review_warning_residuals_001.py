"""Validate residual commercial warning and ASR repairs.

This focused validator covers the true defects identified by the 4E2O audit:
recognized ASR must repair, unsupported positive controls must avoid menus,
out-of-campaign pain phrases need one relevance clarification, no-fit stops
stay classified as intentional, and direct/challenge turns must not menu-loop.
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

from scripts import audit_commercial_review_warning_residuals_001 as audit  # noqa: E402
from scripts import run_live_demo_001_agent_voice_call as demo  # noqa: E402


CHECKPOINT_ID = "COMMERCIAL-REVIEW-WARNING-RESIDUALS-001"
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

GENERIC_CAMPAIGNS = [campaign for campaign in CAMPAIGNS if campaign["config_path"]]
NON_AUTOMOTIVE_GENERIC_CAMPAIGNS = [
    campaign for campaign in GENERIC_CAMPAIGNS if campaign["id"] != "synthetic-automotive-service-review"
]

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
REPAIR_PATTERNS = ("repeat", "rephrase", "misheard", "caught")
APPOINTMENT_PATTERNS = ("callback window", "schedule", "book", "appointment")
ROUTESIGNAL_LEAKS = ("routesignal", "northstar", "$29", "$59", "missed callbacks", "demo follow-up")
FAKE_SIDE_EFFECT_CLAIMS = ("i sent", "i have sent", "calendar invite", "crm", "booked")
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


def contains_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(pattern in text for pattern in patterns)


def is_full_menu(packet: dict[str, Any]) -> bool:
    return contains_any(lower_response(packet), FULL_MENU_PATTERNS)


def asks_repair(packet: dict[str, Any]) -> bool:
    return contains_any(lower_response(packet), REPAIR_PATTERNS)


def appointment_ask(packet: dict[str, Any]) -> bool:
    return contains_any(lower_response(packet), APPOINTMENT_PATTERNS)


def no_fake_claims(packet: dict[str, Any]) -> bool:
    return not contains_any(lower_response(packet), FAKE_SIDE_EFFECT_CLAIMS)


def has_side_effects(packet: dict[str, Any]) -> bool:
    return any(side_effect_flags(packet).values())


def add_failure(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def summarize_packet(packet: dict[str, Any]) -> dict[str, Any]:
    fr = frame(packet)
    mem = memory(packet)
    return {
        "response": response(packet),
        "call_control": call_control(packet),
        "selected_action_source": source(packet),
        "buyer_move_id": fr.get("buyer_move_id"),
        "recognition_reason": fr.get("recognition_reason"),
        "appointment_readiness": fr.get("appointment_readiness"),
        "target_gap": (packet.get("summary") or {}).get("target_gap"),
        "semantic": (packet.get("summary") or {}).get("semantic"),
        "confirmed_gaps": mem.get("confirmed_gaps") or [],
        "side_effect_flags": side_effect_flags(packet),
    }


def validate_asr_recognized_must_repair() -> list[dict[str, Any]]:
    results = []
    for campaign in [CAMPAIGNS[0], *GENERIC_CAMPAIGNS[:3]]:
        packets = run_sequence(
            campaign,
            ["__agent_open__", "yeah sure", "repeal timings are usually pretty long"],
            f"asr-recognized-{slug(campaign['id'])}",
        )
        packet = packets[-1]
        fr = frame(packet)
        failures: list[str] = []
        if fr.get("buyer_move_id") == "asr_garbled_or_low_confidence":
            add_failure(failures, asks_repair(packet), "recognized ASR garble did not ask repeat/rephrase")
        add_failure(failures, not is_full_menu(packet), "ASR repair returned a full menu")
        add_failure(failures, not appointment_ask(packet), "ASR repair asked for appointment")
        add_failure(failures, (packet.get("summary") or {}).get("semantic") != "pain_confirmed", "ASR repair inferred pain")
        add_failure(failures, call_control(packet) == "continue-call", "ASR repair did not continue call")
        add_failure(failures, not has_side_effects(packet), "ASR repair caused side effects")
        results.append(record("asr_recognized_must_repair", campaign, packet, failures))
    return results


def validate_generic_positive_ack_no_menu() -> list[dict[str, Any]]:
    results = []
    for campaign in GENERIC_CAMPAIGNS:
        packets = run_sequence(campaign, ["__agent_open__", "yeah that would be good"], f"positive-ack-{slug(campaign['id'])}")
        packet = packets[-1]
        failures: list[str] = []
        add_failure(
            failures,
            frame(packet).get("buyer_move_id") in {"permission_acknowledgement", "appointment_interest"},
            "positive acknowledgement recognized as unexpected move",
        )
        add_failure(failures, not is_full_menu(packet), "positive acknowledgement returned full menu")
        add_failure(failures, not contains_any(lower_response(packet), ("stop here", "leave it there")), "positive acknowledgement used stop-offer default")
        add_failure(failures, not appointment_ask(packet), "positive acknowledgement asked appointment too early")
        add_failure(failures, call_control(packet) == "continue-call", "positive acknowledgement did not continue call")
        add_failure(failures, not has_side_effects(packet), "positive acknowledgement caused side effects")
        results.append(record("generic_positive_ack_no_menu", campaign, packet, failures))
    return results


def validate_out_of_campaign_pain_phrase() -> list[dict[str, Any]]:
    results = []
    for campaign in NON_AUTOMOTIVE_GENERIC_CAMPAIGNS:
        packets = run_sequence(
            campaign,
            ["__agent_open__", "yeah sure", "repair timings are usually pretty long"],
            f"out-of-campaign-pain-{slug(campaign['id'])}",
        )
        packet = packets[-1]
        failures: list[str] = []
        add_failure(failures, not is_full_menu(packet), "out-of-campaign pain returned full menu")
        add_failure(failures, (packet.get("summary") or {}).get("semantic") != "pain_confirmed", "out-of-campaign pain was falsely confirmed")
        add_failure(
            failures,
            contains_any(lower_response(packet), ("outside this call", "quick check", "happening now", "this call's scope")),
            "out-of-campaign pain did not give one scope/relevance clarification",
        )
        add_failure(failures, not contains_any(lower_response(packet), ROUTESIGNAL_LEAKS), "out-of-campaign pain leaked RouteSignal wording")
        add_failure(failures, call_control(packet) == "continue-call", "out-of-campaign pain did not continue call")
        add_failure(failures, not has_side_effects(packet), "out-of-campaign pain caused side effects")
        results.append(record("out_of_campaign_pain_phrase", campaign, packet, failures))
    automotive = CAMPAIGNS[3]
    packets = run_sequence(
        automotive,
        ["__agent_open__", "yeah sure", "repair timings are usually pretty long"],
        "automotive-clean-pain-control",
    )
    packet = packets[-1]
    failures: list[str] = []
    add_failure(failures, frame(packet).get("buyer_move_id") == "pain_confirmed", "automotive repair timing did not confirm pain")
    add_failure(failures, "repair_timing" in (memory(packet).get("confirmed_gaps") or []), "automotive repair timing target gap lost")
    add_failure(failures, not is_full_menu(packet), "automotive repair timing returned full menu")
    add_failure(failures, not has_side_effects(packet), "automotive repair timing caused side effects")
    results.append(record("automotive_clean_pain_control", automotive, packet, failures))
    return results


def validate_no_fit_stop_classified() -> list[dict[str, Any]]:
    results = []
    for campaign in CAMPAIGNS:
        for transcript in ["not interested", "I don't want to continue", "stop calling"]:
            packets = run_sequence(campaign, ["__agent_open__", transcript], f"no-fit-{slug(campaign['id'])}-{slug(transcript)}")
            packet = packets[-1]
            pseudo_conversation = {"arc_type": "no_fit_stop", "campaign_id": campaign["id"]}
            pseudo_turn = {
                "buyer_utterance": transcript,
                "final_response": response(packet),
                "mechanical_warning_flags": ["over_deferential_stop_offer"] if "stop" in lower_response(packet) else [],
                "selected_action": (packet.get("dialogue_manager") or {}).get("selected_action") or {},
                "universal_policy_frame": frame(packet),
            }
            classification = audit.classify_warning(pseudo_conversation, pseudo_turn, "over_deferential_stop_offer")
            failures: list[str] = []
            add_failure(failures, call_control(packet) in {"end-call", "continue-call"}, "stop turn returned invalid call control")
            add_failure(failures, not appointment_ask(packet), "stop turn continued sales with appointment ask")
            add_failure(failures, classification == "intentional_no_fit_or_stop", "stop warning not classified as intentional")
            add_failure(failures, not has_side_effects(packet), "stop turn caused side effects")
            results.append(record("no_fit_stop_classified", campaign, packet, failures, buyer_utterance=transcript))
    return results


def validate_direct_question_no_menu_loop() -> list[dict[str, Any]]:
    results = []
    for campaign in CAMPAIGNS:
        packets = run_sequence(
            campaign,
            ["__agent_open__", "what does your product do", "why should I care"],
            f"direct-question-{slug(campaign['id'])}",
        )
        for index, packet in enumerate(packets[1:], start=1):
            failures: list[str] = []
            add_failure(failures, frame(packet).get("buyer_move_id") in {"product_detail_question", "why_should_i_care"}, "direct question recognized incorrectly")
            add_failure(failures, response(packet).strip() != "", "direct question had empty response")
            add_failure(failures, not is_full_menu(packet), "direct question returned full menu")
            add_failure(failures, "approved qualified reviewer path" not in lower_response(packet), "direct question used internal wording")
            add_failure(failures, response(packet).count("?") <= 1, "direct question asked more than one next action")
            add_failure(failures, no_fake_claims(packet), "direct question made fake side-effect claim")
            add_failure(failures, not has_side_effects(packet), "direct question caused side effects")
            results.append(record(f"direct_question_no_menu_loop_{index}", campaign, packet, failures))
    return results


def validate_confusion_loop_resistance() -> list[dict[str, Any]]:
    results = []
    for campaign in CAMPAIGNS:
        packets = run_sequence(
            campaign,
            ["__agent_open__", "yeah sure", campaign["pain"], "what do you mean", "you already asked that", "you didn't answer my question"],
            f"confusion-loop-{slug(campaign['id'])}",
        )
        for transcript, packet in zip(["what do you mean", "you already asked that", "you didn't answer my question"], packets[-3:]):
            failures: list[str] = []
            add_failure(
                failures,
                frame(packet).get("buyer_move_id") in {"confusion_not_clear", "already_answered_challenge"},
                "challenge recognized incorrectly",
            )
            add_failure(failures, not is_full_menu(packet), "challenge returned full menu")
            add_failure(failures, source(packet) != "pre_speech_conversation_stability_guard", "challenge was taken over by stability guard")
            add_failure(failures, source(packet) != "duplicate_response_repair", "challenge was taken over by duplicate repair")
            add_failure(failures, campaign["expected_gap"] in (memory(packet).get("confirmed_gaps") or []), "confirmed gap was not preserved")
            add_failure(failures, no_fake_claims(packet), "challenge made fake side-effect claim")
            add_failure(failures, not has_side_effects(packet), "challenge caused side effects")
            results.append(record("confusion_loop_resistance", campaign, packet, failures, buyer_utterance=transcript))
    return results


def record(
    scenario: str,
    campaign: dict[str, Any],
    packet: dict[str, Any],
    failures: list[str],
    *,
    buyer_utterance: str | None = None,
) -> dict[str, Any]:
    return {
        "scenario": scenario,
        "campaign": campaign["id"],
        "buyer_utterance": buyer_utterance or str(packet.get("transcript") or ""),
        "passed": not failures,
        "failures": failures,
        "packet": summarize_packet(packet),
    }


def summarize(results: list[dict[str, Any]], audit_result: dict[str, Any]) -> dict[str, Any]:
    failure_counter: Counter[str] = Counter()
    scenario_counter: Counter[str] = Counter()
    for result in results:
        if result["passed"]:
            continue
        scenario_counter[result["scenario"]] += 1
        failure_counter.update(result["failures"])
    return {
        "scenario_count": len(results),
        "pass_count": sum(1 for item in results if item["passed"]),
        "failure_count": sum(1 for item in results if not item["passed"]),
        "failure_counts_by_scenario": dict(scenario_counter.most_common()),
        "top_failures": dict(failure_counter.most_common(12)),
        "audit_true_sales_defect_count": audit_result.get("true_sales_defect_count"),
        "audit_true_asr_repair_defect_count": audit_result.get("true_asr_repair_defect_count"),
        "audit_commercial_warning_classification_counts": audit_result.get("commercial_warning_classification_counts"),
        "audit_asr_residual_classification_counts": audit_result.get("asr_residual_classification_counts"),
    }


def write_evidence(result: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    summary = result["summary"]
    lines = [
        f"# {CHECKPOINT_ID}",
        "",
        "## 1. Summary",
        "Validated residual warning and ASR cleanup scenarios using dry-run turn builders only.",
        "",
        "## 2. Scenario Counts",
        f"- Scenarios: {summary['scenario_count']}",
        f"- Pass/fail: {summary['pass_count']} / {summary['failure_count']}",
        "",
        "## 3. Failure Counts By Scenario",
    ]
    for scenario, count in summary["failure_counts_by_scenario"].items():
        lines.append(f"- {scenario}: {count}")
    lines.extend(["", "## 4. Top Failures"])
    for failure, count in summary["top_failures"].items():
        lines.append(f"- {failure}: {count}")
    lines.extend(["", "## 5. Audit Classification Snapshot"])
    lines.append(f"- True sales defects: {summary['audit_true_sales_defect_count']}")
    lines.append(f"- True ASR repair defects: {summary['audit_true_asr_repair_defect_count']}")
    lines.extend(["", "## 6. Safety Boundary Summary"])
    lines.append("- Provider, local LLM, live TTS, email, calendar, CRM, PROD-102, and customer-audio upload side effects remained false in validator scenarios.")
    lines.extend(["", "## 7. Runtime Behavior Changed"])
    lines.append("- Yes, if this validator is run after the associated runtime patch; otherwise this file records the focused red/green checkpoint.")
    (OUT_DIR / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    audit_result = audit.build_result()
    results: list[dict[str, Any]] = []
    results.extend(validate_asr_recognized_must_repair())
    results.extend(validate_generic_positive_ack_no_menu())
    results.extend(validate_out_of_campaign_pain_phrase())
    results.extend(validate_no_fit_stop_classified())
    results.extend(validate_direct_question_no_menu_loop())
    results.extend(validate_confusion_loop_resistance())
    summary = summarize(results, audit_result)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "pass" if summary["failure_count"] == 0 else "fail",
        "summary": summary,
        "results": results,
        "side_effects": {key: False for key in SIDE_EFFECT_KEYS},
        "runtime_behavior_changed_scope": "ASR repair precedence, out-of-campaign pain clarification, and challenge loop repair only.",
    }
    write_evidence(result)
    print(
        json.dumps(
            {
                "checkpoint_id": CHECKPOINT_ID,
                "status": result["status"],
                "pass_count": summary["pass_count"],
                "failure_count": summary["failure_count"],
                "top_failures": summary["top_failures"],
                "output_dir": OUT_DIR.as_posix(),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
