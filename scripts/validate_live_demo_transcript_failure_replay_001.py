#!/usr/bin/env python3
"""Replay current-runtime live transcript failures before patching behavior."""

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


CHECKPOINT_ID = "LIVE-DEMO-TRANSCRIPT-FAILURE-REPLAY-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID
EXAMPLES = ROOT / "runtime" / "campaigns" / "examples"

ROUTESIGNAL = {"id": "routesignal_live_demo", "config_path": None}
INSURANCE = {"id": "synthetic-insurance-review", "config_path": EXAMPLES / "synthetic-insurance-review.json"}
TELECOM = {"id": "synthetic-telecom-plan-review", "config_path": EXAMPLES / "synthetic-telecom-plan-review.json"}

FULL_MENU_PATTERNS = (
    "which part is least clear",
    "which part is more familiar",
    "name the point: workflow, price, security",
    "missed callbacks, manual tracking, or handoffs",
    "routing, callbacks, or handoffs",
    "manual tracking or missed callbacks",
    "premium, coverage fit, or renewal",
    "premium or budget, coverage fit, or renewal",
    "plan fit, coverage or availability, or contract or switching",
    "plan fit, coverage, or availability, or contract or switching",
    "which part should i check first",
)

INTERNAL_PATTERNS = (
    "approved qualified reviewer path",
    "i should not",
    "i should stick",
    "approved details",
    "internal policy",
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

REPRODUCED_BEFORE_PATCH_SCENARIOS = {
    "routesignal_permission_repeated_ack",
    "routesignal_asr_near_miss_callbacks",
    "routesignal_near_miss_then_impact",
    "routesignal_vague_followup_little_bit",
    "routesignal_why_care_challenge",
    "insurance_false_assumption_correction",
    "insurance_repeated_product_detail_challenge",
    "telecom_vague_positive_after_prior_bad_experience",
    "telecom_plan_fit_coverage_boundary",
}

PRESERVATION_SCENARIOS = {
    "preserve_driving_stop",
    "preserve_hospital_stop",
    "preserve_direct_product_answer",
    "preserve_ai_disclosure",
    "preserve_callback_time_capture",
}

CLASSIFICATION_LABELS = (
    "reproduced_before_patch_then_fixed",
    "not_reproduced_on_current_runtime",
    "preservation_check_passed",
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


def question_count(packet: dict[str, Any]) -> int:
    return response(packet).count("?")


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


def add_failure(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def common_checks(packet: dict[str, Any], failures: list[str]) -> None:
    lower = lower_response(packet)
    add_failure(failures, not contains_any(lower, FULL_MENU_PATTERNS), "response used menu or broad point picker")
    add_failure(failures, not contains_any(lower, INTERNAL_PATTERNS), "response used internal wording")
    add_failure(failures, question_count(packet) <= 1, "response asked more than one question")
    add_failure(failures, call_control(packet) == "continue-call", f"call_control was {call_control(packet)!r}")
    add_failure(failures, not any(side_effect_flags(packet).values()), "side effects were not all false")


def summarize(packet: dict[str, Any], transcript: str) -> dict[str, Any]:
    fr = frame(packet)
    return {
        "transcript": transcript,
        "response": response(packet),
        "call_control": call_control(packet),
        "selected_action_source": selected_source(packet),
        "buyer_move_id": fr.get("buyer_move_id"),
        "buyer_move_category": fr.get("buyer_move_category"),
        "recognition_reason": fr.get("recognition_reason"),
        "response_shape_enforced_category": fr.get("response_shape_enforced_category"),
        "appointment_readiness": fr.get("appointment_readiness"),
        "confirmed_gap_id": fr.get("confirmed_gap_id"),
        "confirmed_gap_phrase": fr.get("confirmed_gap_phrase"),
        "side_effect_flags": side_effect_flags(packet),
    }


def classify(scenario: str, failures: list[str]) -> str:
    if scenario in PRESERVATION_SCENARIOS:
        return "preservation_check_passed" if not failures else "preservation_check_failed"
    if scenario in REPRODUCED_BEFORE_PATCH_SCENARIOS:
        return "reproduced_before_patch_then_fixed" if not failures else "reproduced_before_patch_still_failing"
    return "not_reproduced_on_current_runtime"


def scenario_permission_ack() -> dict[str, Any]:
    turns = ["__agent_open__", "sure sure"]
    packets = run_sequence(ROUTESIGNAL, turns, "4f2a-routesignal-permission")
    last = packets[-1]
    failures: list[str] = []
    common_checks(last, failures)
    fr = frame(last)
    lower = lower_response(last)
    add_failure(failures, fr.get("buyer_move_id") == "permission_acknowledgement", "permission acknowledgement not recognized")
    add_failure(failures, "inbound demo follow-up" in lower and ("slipping" in lower or "happening" in lower), "response did not ask sharp RouteSignal diagnostic")
    add_failure(failures, selected_source(last) != "pre_speech_conversation_stability_guard", "stability guard overrode permission path")
    scenario = "routesignal_permission_repeated_ack"
    return {"scenario": scenario, "passed": not failures, "classification": classify(scenario, failures), "failures": failures, "packet": summarize(last, turns[-1])}


def scenario_asr_near_miss_callbacks() -> dict[str, Any]:
    turns = ["__agent_open__", "sure sure", "call bags are a problem"]
    packets = run_sequence(ROUTESIGNAL, turns, "4f2a-routesignal-call-bags")
    last = packets[-1]
    failures: list[str] = []
    common_checks(last, failures)
    lower = lower_response(last)
    fr = frame(last)
    acceptable_move = fr.get("buyer_move_id") in {"asr_near_miss_for_known_gap", "pain_confirmed", "tentative_gap_interest", "confusion_not_clear"}
    acceptable_response = (
        "did you mean callbacks" in lower
        or "heard that as callbacks" in lower
        or ("callbacks are the issue" in lower and ("missed follow-up" in lower or "extra tracking" in lower))
        or ("callbacks" in lower and "impact" in lower)
    )
    add_failure(failures, acceptable_move, f"unexpected buyer_move_id {fr.get('buyer_move_id')!r}")
    add_failure(failures, acceptable_response, "response did not clarify or map callbacks near-miss")
    add_failure(failures, selected_source(last) != "pre_speech_conversation_stability_guard", "stability guard overrode ASR near-miss")
    scenario = "routesignal_asr_near_miss_callbacks"
    return {"scenario": scenario, "passed": not failures, "classification": classify(scenario, failures), "failures": failures, "packet": summarize(last, turns[-1])}


def scenario_near_miss_then_impact() -> dict[str, Any]:
    turns = ["__agent_open__", "sure sure", "call bags are a problem", "I mean it causes delays so that is a problem for us"]
    packets = run_sequence(ROUTESIGNAL, turns, "4f2a-routesignal-call-bags-impact")
    last = packets[-1]
    failures: list[str] = []
    common_checks(last, failures)
    lower = lower_response(last)
    fr = frame(last)
    add_failure(failures, "outside this call" not in lower and "outside scope" not in lower, "response treated impact as out of scope")
    add_failure(failures, "inbound demo follow-up slipping is causing any issue now" not in lower, "response reset to generic inbound demo question")
    add_failure(failures, "delay" in lower or "delays" in lower or fr.get("buyer_move_id") == "implication_confirmed", "response did not preserve impact")
    add_failure(failures, fr.get("appointment_readiness") in {"medium", "high"} or fr.get("buyer_move_id") in {"implication_confirmed", "pain_confirmed", "asr_near_miss_for_known_gap"}, "impact did not advance or preserve likely gap")
    scenario = "routesignal_near_miss_then_impact"
    return {"scenario": scenario, "passed": not failures, "classification": classify(scenario, failures), "failures": failures, "packet": summarize(last, turns[-1])}


def scenario_vague_followup() -> dict[str, Any]:
    turns = ["__agent_open__", "sure sure", "call bags are a problem", "I guess a little bit"]
    packets = run_sequence(ROUTESIGNAL, turns, "4f2a-routesignal-little-bit")
    last = packets[-1]
    failures: list[str] = []
    common_checks(last, failures)
    lower = lower_response(last)
    add_failure(failures, "a little bit" in lower or "minor annoyance" in lower or "minor" in lower, "vague weak pain was not acknowledged")
    add_failure(failures, "name the point" not in lower, "vague weak pain routed to product detail point picker")
    scenario = "routesignal_vague_followup_little_bit"
    return {"scenario": scenario, "passed": not failures, "classification": classify(scenario, failures), "failures": failures, "packet": summarize(last, turns[-1])}


def scenario_why_care_challenge() -> dict[str, Any]:
    turns = ["__agent_open__", "I do but what does your product do", "what should I care"]
    packets = run_sequence(ROUTESIGNAL, turns, "4f2a-routesignal-why-care")
    last = packets[-1]
    failures: list[str] = []
    common_checks(last, failures)
    lower = lower_response(last)
    add_failure(failures, frame(last).get("buyer_move_id") == "why_should_i_care", "why-care variant not recognized")
    add_failure(failures, "fair question" in lower and ("costing time" in lower or "delays" in lower or "missed replies" in lower), "why-care challenge not answered directly")
    add_failure(failures, "name the point" not in lower, "why-care routed to point picker")
    scenario = "routesignal_why_care_challenge"
    return {"scenario": scenario, "passed": not failures, "classification": classify(scenario, failures), "failures": failures, "packet": summarize(last, turns[-1])}


def scenario_insurance_false_assumption() -> dict[str, Any]:
    turns = ["__agent_open__", "yeah", "what does your product do can you give me any details", "I did not mention premium"]
    packets = run_sequence(INSURANCE, turns, "4f2a-insurance-false-assumption")
    last = packets[-1]
    failures: list[str] = []
    common_checks(last, failures)
    lower = lower_response(last)
    add_failure(failures, "you did not mention premium" in lower or "didn't mention premium" in lower, "premium correction not acknowledged")
    add_failure(failures, "should not assume" in lower or "won't assume" in lower, "false premium assumption not removed")
    add_failure(failures, "since you mentioned premium" not in lower, "continued false premium assumption")
    add_failure(failures, "licensed" in lower or "review" in lower, "scope not explained after correction")
    scenario = "insurance_false_assumption_correction"
    return {"scenario": scenario, "passed": not failures, "classification": classify(scenario, failures), "failures": failures, "packet": summarize(last, turns[-1])}


def scenario_insurance_repeated_product_detail() -> dict[str, Any]:
    turns = [
        "__agent_open__",
        "yeah",
        "what does your product do can you give me any details",
        "I did not mention premium",
        "so can you not give me any details",
    ]
    packets = run_sequence(INSURANCE, turns, "4f2a-insurance-scope-repeat")
    last = packets[-1]
    failures: list[str] = []
    common_checks(last, failures)
    lower = lower_response(last)
    add_failure(failures, frame(last).get("buyer_move_id") == "scope_limit_question", "scope limit question not recognized")
    add_failure(failures, "high-level" in lower or "purpose of the call" in lower or "licensed" in lower, "capability boundary not answered directly")
    add_failure(failures, "which part should i check first" not in lower, "scope question reopened full menu")
    scenario = "insurance_repeated_product_detail_challenge"
    return {"scenario": scenario, "passed": not failures, "classification": classify(scenario, failures), "failures": failures, "packet": summarize(last, turns[-1])}


def scenario_telecom_vague_positive_after_bad_experience() -> dict[str, Any]:
    turns = ["__agent_open__", "yeah start with how much is your product", "I'm asking because the last company wasted my time", "yeah that'd be good"]
    packets = run_sequence(TELECOM, turns, "4f2a-telecom-vague-positive")
    last = packets[-1]
    failures: list[str] = []
    common_checks(last, failures)
    lower = lower_response(last)
    add_failure(failures, "one concrete check" in lower or ("plan fit" in lower and ("coverage" in lower or "availability" in lower)), "vague positive did not accept one-check frame")
    add_failure(failures, "contract or switching" not in lower, "vague positive reopened full telecom menu")
    scenario = "telecom_vague_positive_after_prior_bad_experience"
    return {"scenario": scenario, "passed": not failures, "classification": classify(scenario, failures), "failures": failures, "packet": summarize(last, turns[-1])}


def scenario_telecom_plan_fit_boundary() -> dict[str, Any]:
    turns = [
        "__agent_open__",
        "yeah start with how much is your product",
        "I'm asking because the last company wasted my time",
        "yeah that'd be good",
        "how about the plane fit and coverage",
    ]
    packets = run_sequence(TELECOM, turns, "4f2a-telecom-plan-fit-boundary")
    last = packets[-1]
    failures: list[str] = []
    common_checks(last, failures)
    lower = lower_response(last)
    add_failure(failures, "telecom account specialist" in lower or "specialist" in lower, "customer-facing specialist boundary missing")
    add_failure(failures, "plan fit" in lower and ("availability" in lower or "coverage" in lower), "plan fit/coverage context not preserved")
    add_failure(failures, "is that what you want" in lower or "want them to check" in lower, "one review-confirmation question missing")
    add_failure(failures, call_control(last) != "transfer-or-escalate", "boundary escalated abruptly")
    scenario = "telecom_plan_fit_coverage_boundary"
    return {"scenario": scenario, "passed": not failures, "classification": classify(scenario, failures), "failures": failures, "packet": summarize(last, turns[-1])}


def preservation_scenarios() -> list[dict[str, Any]]:
    specs = [
        ("preserve_driving_stop", ROUTESIGNAL, ["__agent_open__", "I'm driving"], lambda p: call_control(p) == "end-call" and "driving" in lower_response(p)),
        ("preserve_hospital_stop", ROUTESIGNAL, ["__agent_open__", "I just got out of the hospital"], lambda p: call_control(p) == "end-call" and "sorry" in lower_response(p)),
        ("preserve_direct_product_answer", ROUTESIGNAL, ["__agent_open__", "what does your product do"], lambda p: frame(p).get("buyer_move_id") == "product_detail_question" and question_count(p) <= 1),
        ("preserve_ai_disclosure", ROUTESIGNAL, ["__agent_open__", "are you a robot"], lambda p: frame(p).get("buyer_move_id") == "are_you_ai_or_robot" and "ai voice agent" in lower_response(p)),
        ("preserve_callback_time_capture", ROUTESIGNAL, ["__agent_open__", "sure sure", "callbacks are a problem", "it causes delays", "tomorrow at 3 works"], lambda p: frame(p).get("buyer_move_id") == "callback_time_provided" and call_control(p) in {"continue-call", "schedule-and-end"}),
    ]
    records: list[dict[str, Any]] = []
    for label, campaign, turns, predicate in specs:
        packets = run_sequence(campaign, list(turns), f"4f2a-{label}")
        last = packets[-1]
        failures: list[str] = []
        add_failure(failures, predicate(last), f"{label} did not preserve expected behavior")
        add_failure(failures, not any(side_effect_flags(last).values()), "side effects were not all false")
        records.append({"scenario": label, "passed": not failures, "classification": classify(label, failures), "failures": failures, "packet": summarize(last, turns[-1])})
    return records


def run_matrix() -> list[dict[str, Any]]:
    return [
        scenario_permission_ack(),
        scenario_asr_near_miss_callbacks(),
        scenario_near_miss_then_impact(),
        scenario_vague_followup(),
        scenario_why_care_challenge(),
        scenario_insurance_false_assumption(),
        scenario_insurance_repeated_product_detail(),
        scenario_telecom_vague_positive_after_bad_experience(),
        scenario_telecom_plan_fit_boundary(),
        *preservation_scenarios(),
    ]


def write_outputs(records: list[dict[str, Any]]) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    failure_count = sum(1 for record in records if not record["passed"])
    raw_classification_counts = Counter(str(record.get("classification") or "") for record in records)
    classification_counts = {label: raw_classification_counts.get(label, 0) for label in CLASSIFICATION_LABELS}
    for label, count in sorted(raw_classification_counts.items()):
        if label not in classification_counts:
            classification_counts[label] = count
    side_effects = {
        "provider_calls_made": False,
        "local_llm_calls_made": False,
        "sends_email": False,
        "creates_calendar_event": False,
        "writes_crm": False,
        "opens_prod_102": False,
        "customer_audio_uploaded_to_python_server": False,
        "customer_audio_uploaded_to_tts_provider": False,
    }
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "pass" if failure_count == 0 else "fail",
        "matrix_size": len(records),
        "pass_count": len(records) - failure_count,
        "failure_count": failure_count,
        "classification_counts": classification_counts,
        "runtime_behavior_changed": False,
        "known_reproduced_before_patch_count": len(REPRODUCED_BEFORE_PATCH_SCENARIOS),
        "preservation_check_count": len(PRESERVATION_SCENARIOS),
        "records": records,
        "side_effects": side_effects,
    }
    report_lines = [
        f"# {CHECKPOINT_ID}",
        "",
        "## Summary",
        f"- Status: `{result['status']}`",
        f"- Matrix size: `{result['matrix_size']}`",
        f"- Pass count: `{result['pass_count']}`",
        f"- Failure count: `{result['failure_count']}`",
        f"- Runtime behavior changed in this phase: `{str(result['runtime_behavior_changed']).lower()}`",
        f"- Known reproduced-before-patch scenarios: `{result['known_reproduced_before_patch_count']}`",
        f"- Preservation scenarios: `{result['preservation_check_count']}`",
        "",
        "## Classification Counts",
        *(f"- `{key}`: `{value}`" for key, value in result["classification_counts"].items()),
        "",
        "## Classification Meaning",
        "- `reproduced_before_patch_then_fixed`: scenario failed during the 4F2A red replay and now passes on the current runtime.",
        "- `not_reproduced_on_current_runtime`: scenario did not reproduce as a current runtime failure.",
        "- `preservation_check_passed`: guard scenario for existing safe behavior; it was not one of the live transcript failures.",
        "",
        "## Scenario Results",
    ]
    for record in records:
        report_lines.extend(
            [
                f"### {record['scenario']}",
                f"- Passed: `{str(record['passed']).lower()}`",
                f"- Classification: `{record['classification']}`",
                f"- Buyer move: `{record['packet'].get('buyer_move_id')}`",
                f"- Source: `{record['packet'].get('selected_action_source')}`",
                f"- Call control: `{record['packet'].get('call_control')}`",
                f"- Response: {record['packet'].get('response')}",
            ]
        )
        if record["failures"]:
            report_lines.append(f"- Failures: `{'; '.join(record['failures'])}`")
        report_lines.append("")
    (OUT_DIR / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT_DIR / "report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    return result


def main() -> None:
    result = write_outputs(run_matrix())
    print(json.dumps({k: result[k] for k in ("checkpoint_id", "status", "matrix_size", "pass_count", "failure_count", "classification_counts")}, indent=2, sort_keys=True))
    if result["failure_count"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
