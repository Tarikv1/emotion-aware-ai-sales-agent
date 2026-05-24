#!/usr/bin/env python3
"""Replay current live-derived dialogue cracks against the local runtime."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
import sys
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import run_live_demo_001_agent_voice_call as demo  # noqa: E402


CHECKPOINT_ID = "CURRENT-LIVE-TRANSCRIPT-REPLAY-001"
OFFER_SCOPE_CHECKPOINT_ID = "CAMPAIGN-OFFER-SCOPE-MODEL-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
OFFER_SCOPE_OUT_DIR = ROOT / "research" / "experiments" / "generated" / OFFER_SCOPE_CHECKPOINT_ID
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID
EXAMPLES = ROOT / "runtime" / "campaigns" / "examples"

ROUTESIGNAL = {"id": "routesignal", "config_path": None}
TELECOM = {"id": "synthetic-telecom-plan-review", "config_path": EXAMPLES / "synthetic-telecom-plan-review.json"}
INSURANCE = {"id": "synthetic-insurance-review", "config_path": EXAMPLES / "synthetic-insurance-review.json"}

REQUIRED_OFFER_FIELDS = (
    "product_or_offer_name",
    "product_or_offer_summary",
    "high_level_value_proposition",
    "allowed_high_level_capabilities",
    "agent_call_objective",
    "appointment_target",
    "human_followup_owner",
    "human_review_scope",
    "agent_can_say",
    "agent_must_not_claim",
)

FORBIDDEN_RESPONSE_PATTERNS = (
    "quick check: are demo leads missing an owner or next reply right now",
    "i can answer that directly if you name the point",
    "the high-level answer is covered",
    "name the point",
    "approved qualified reviewer path",
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


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
    add_failure(failures, not contains_any(lower, FORBIDDEN_RESPONSE_PATTERNS), "response used forbidden live-crack wording")
    add_failure(failures, question_count(packet) <= 1, "response asked more than one question")
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
        "side_effect_flags": side_effect_flags(packet),
    }


def route_signal_product_answer(packet: dict[str, Any], failures: list[str]) -> None:
    lower = lower_response(packet)
    common_checks(packet, failures)
    add_failure(failures, frame(packet).get("buyer_move_id") in {"what_problem_do_you_solve", "product_detail_question"}, "direct product question not recognized")
    add_failure(failures, "routesignal" in lower, "RouteSignal name missing from product answer")
    add_failure(failures, "crm" in lower or "workflow tool" in lower or "workflow product" in lower, "CRM/workflow product category missing")
    add_failure(failures, "inbound demo" in lower and ("follow-up" in lower or "follow up" in lower), "inbound demo follow-up value missing")
    add_failure(failures, selected_source(packet) != "pre_speech_conversation_stability_guard", "stability guard overrode direct product answer")


def route_signal_process_answer(packet: dict[str, Any], failures: list[str]) -> None:
    lower = lower_response(packet)
    common_checks(packet, failures)
    add_failure(failures, not lower.startswith("i'm good") and not lower.startswith("im good"), "process question treated as small talk")
    add_failure(failures, "review" in lower or "check" in lower or "look at" in lower, "review/check process missing")
    add_failure(failures, contains_any(lower, ("owner", "owns", "follow-up", "follow up", "reminder", "handoff")), "workflow review scope missing")
    add_failure(failures, contains_any(lower, ("high level", "high-level", "i can only", "specialist", "reviewer")), "safe capability boundary missing")


def callback_near_miss_answer(packet: dict[str, Any], failures: list[str], *, ambiguous: bool) -> None:
    lower = lower_response(packet)
    common_checks(packet, failures)
    if ambiguous:
        add_failure(failures, "did you mean callbacks" in lower or "misheard" in lower, "ambiguous callback near-miss was not clarified")
        add_failure(failures, "outside" not in lower and "out of scope" not in lower, "ambiguous callback near-miss was rejected")
    else:
        add_failure(failures, "callbacks" in lower, "callback context not preserved")
        add_failure(failures, "outside" not in lower and "out of scope" not in lower, "callback variant treated as out of scope")


def callback_negative_control(packet: dict[str, Any], failures: list[str]) -> None:
    lower = lower_response(packet)
    add_failure(failures, "did you mean callbacks" not in lower, "negative control falsely mapped to callback near-miss")
    add_failure(failures, frame(packet).get("confirmed_gap_id") != "callbacks", "negative control confirmed callbacks")
    add_failure(failures, not any(side_effect_flags(packet).values()), "side effects were not all false")


def already_told_answer(packet: dict[str, Any], failures: list[str]) -> None:
    lower = lower_response(packet)
    common_checks(packet, failures)
    add_failure(failures, "causing delays or extra work" not in lower and "is it causing" not in lower, "impact question was repeated after full capture")
    add_failure(failures, "already" in lower or "right" in lower, "already-told-you challenge not acknowledged")
    add_failure(failures, "callbacks" in lower and ("delays" in lower or "delay" in lower), "captured issue and impact not summarized")
    add_failure(failures, "tomorrow" in lower or "3" in lower or "time" in lower, "captured callback time not preserved")


def appointment_answer(packet: dict[str, Any], failures: list[str]) -> None:
    lower = lower_response(packet)
    common_checks(packet, failures)
    add_failure(failures, "yes" in lower or "next step" in lower, "appointment question not answered directly")
    add_failure(failures, "review" in lower and ("callback" in lower or "window" in lower or "time" in lower), "review/callback next step not explained")
    add_failure(failures, "not booking" in lower or "not book" in lower or "not a calendar" in lower or "not booking a calendar" in lower, "calendar booking boundary missing")


def stop_answer(packet: dict[str, Any], failures: list[str]) -> None:
    common_checks(packet, failures)
    add_failure(failures, call_control(packet) == "end-call", f"stop variant did not end call: {call_control(packet)!r}")
    add_failure(failures, "stop" in lower_response(packet) or "goodbye" in lower_response(packet), "stop response did not close politely")


def stop_negative(packet: dict[str, Any], failures: list[str]) -> None:
    add_failure(failures, call_control(packet) != "end-call", "negative stop control incorrectly ended call")
    add_failure(failures, not any(side_effect_flags(packet).values()), "side effects were not all false")


def telecom_product_difference(packet: dict[str, Any], failures: list[str]) -> None:
    lower = lower_response(packet)
    common_checks(packet, failures)
    add_failure(failures, "cannot compare exact" in lower or "can't compare exact" in lower or "cannot compare your exact" in lower, "exact provider comparison boundary missing")
    add_failure(failures, "specialist" in lower or "human" in lower, "human review owner missing")
    add_failure(failures, "plan fit" in lower and ("coverage" in lower or "provider" in lower), "plan fit/coverage comparison scope missing")
    add_failure(failures, "review is the product" not in lower, "review was framed as the product")


def telecom_review_scope(packet: dict[str, Any], failures: list[str]) -> None:
    lower = lower_response(packet)
    common_checks(packet, failures)
    add_failure(failures, "specialist" in lower or "human" in lower, "human review owner missing")
    add_failure(failures, "plan fit" in lower and ("coverage" in lower or "availability" in lower), "plan fit/coverage scope missing")
    add_failure(failures, "review" in lower or "compare" in lower or "check" in lower, "review/check action missing")
    add_failure(failures, "review is the product" not in lower, "review was framed as the product")


def telecom_review_acceptance(packet: dict[str, Any], failures: list[str]) -> None:
    lower = lower_response(packet)
    common_checks(packet, failures)
    add_failure(failures, "callback" in lower or "window" in lower or "time" in lower, "accepted review scope did not move to callback/contact next step")
    add_failure(failures, "is plan fit causing any issue right now" not in lower, "accepted review scope reopened generic plan-fit question")
    add_failure(failures, "quick check for a short human plan and availability review" not in lower, "accepted review scope reset to generic review pitch")


def generic_product_answer(packet: dict[str, Any], failures: list[str], campaign_label: str) -> None:
    lower = lower_response(packet)
    common_checks(packet, failures)
    add_failure(failures, frame(packet).get("buyer_move_id") in {"what_problem_do_you_solve", "product_detail_question"}, f"{campaign_label} product question not recognized")
    add_failure(failures, "review is the product" not in lower, f"{campaign_label} framed review as product")
    add_failure(failures, "synthetic campaign" not in lower and "test fixture" not in lower, f"{campaign_label} leaked fixture wording")
    add_failure(failures, "high-level check" in lower or "fit check" in lower or "fit-check" in lower, f"{campaign_label} offer summary missing")
    add_failure(failures, "review" in lower and ("human" in lower or "specialist" in lower or "licensed" in lower), f"{campaign_label} review boundary missing")


def generic_value_answer(packet: dict[str, Any], failures: list[str], campaign_label: str) -> None:
    lower = lower_response(packet)
    common_checks(packet, failures)
    add_failure(failures, "review is the product" not in lower, f"{campaign_label} framed review as product")
    add_failure(failures, "synthetic campaign" not in lower and "test fixture" not in lower, f"{campaign_label} leaked fixture wording")
    add_failure(failures, "high-level check" in lower or "fit check" in lower or "fit-check" in lower, f"{campaign_label} offer summary missing")
    add_failure(failures, "value" in lower or "useful" in lower or "avoid wasting" in lower or "route" in lower or "specialist" in lower, f"{campaign_label} value boundary missing")


def human_review_answer(packet: dict[str, Any], failures: list[str]) -> None:
    lower = lower_response(packet)
    common_checks(packet, failures)
    add_failure(failures, "human review" in lower or "specialist" in lower or "human" in lower or "reviewer" in lower, "human review not explained")
    add_failure(
        failures,
        "next step" in lower
        or "before any decision" in lower
        or "actual details" in lower
        or "before any recommendation" in lower
        or "worth a callback" in lower
        or "callback window" in lower,
        "review not positioned as next step",
    )
    add_failure(failures, "product" not in lower or "not the product" in lower or "next step" in lower, "human review may be framed as product")


def make_record(
    *,
    group: str,
    scenario: str,
    campaign: dict[str, Any],
    turns: list[str],
    assertion: Callable[[dict[str, Any], list[str]], None],
) -> dict[str, Any]:
    packets = run_sequence(campaign, turns, f"{CHECKPOINT_ID}-{scenario}")
    last = packets[-1]
    failures: list[str] = []
    assertion(last, failures)
    return {
        "group": group,
        "scenario": scenario,
        "campaign_id": campaign["id"],
        "turn_count": len(turns),
        "multi_turn": len(turns) >= 2,
        "passed": not failures,
        "failures": failures,
        "packet": summarize(last, turns[-1]),
    }


def offer_scope_config_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for campaign in (TELECOM, INSURANCE):
        data = json.loads(Path(campaign["config_path"]).read_text(encoding="utf-8"))
        missing = [field for field in REQUIRED_OFFER_FIELDS if field not in data or data.get(field) in ("", [], None)]
        records.append(
            {
                "group": "H_campaign_offer_scope_model_validation",
                "scenario": f"{campaign['id']}_required_offer_fields_present",
                "campaign_id": campaign["id"],
                "turn_count": 0,
                "multi_turn": False,
                "passed": not missing,
                "failures": [f"missing offer-scope fields: {', '.join(missing)}"] if missing else [],
                "packet": {},
            }
        )
    return records


def run_matrix() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    direct_product_variants = [
        "I'm sorry what are you guys selling",
        "what are you selling",
        "what do you guys sell",
        "what is this product",
        "what is RouteSignal",
        "what exactly do you do",
        "what are you calling about",
    ]
    for idx, phrase in enumerate(direct_product_variants):
        records.append(
            make_record(
                group="A_routesignal_direct_product_question",
                scenario=f"routesignal_direct_product_{idx:02d}",
                campaign=ROUTESIGNAL,
                turns=["__agent_open__", phrase],
                assertion=route_signal_product_answer,
            )
        )

    process_variants = [
        "how are you going to check that",
        "how would you check that",
        "how do you review that",
        "what would they look at",
        "what will the specialist do",
    ]
    for idx, phrase in enumerate(process_variants):
        records.append(
            make_record(
                group="B_routesignal_process_explanation",
                scenario=f"routesignal_process_explanation_{idx:02d}",
                campaign=ROUTESIGNAL,
                turns=["__agent_open__", "what are you guys selling", phrase],
                assertion=route_signal_process_answer,
            )
        )

    positive_near_misses = [
        ("colbert's are a problem", True),
        ("call bags are a problem", True),
        ("call backs are a problem", False),
        ("callback issue is a problem", False),
        ("call-back timing is the problem", False),
        ("cold backs are a problem", True),
    ]
    for idx, (phrase, ambiguous) in enumerate(positive_near_misses):
        records.append(
            make_record(
                group="C_routesignal_asr_near_miss_callbacks",
                scenario=f"routesignal_callback_near_miss_{idx:02d}",
                campaign=ROUTESIGNAL,
                turns=["__agent_open__", "sure sure", phrase],
                assertion=lambda packet, failures, ambiguous=ambiguous: callback_near_miss_answer(packet, failures, ambiguous=ambiguous),
            )
        )

    for idx, phrase in enumerate(["coverage is a problem", "insurance coverage should be checked", "Colbert unrelated sentence"]):
        records.append(
            make_record(
                group="C_routesignal_asr_near_miss_negative_controls",
                scenario=f"routesignal_callback_negative_control_{idx:02d}",
                campaign=ROUTESIGNAL,
                turns=["__agent_open__", "sure sure", phrase],
                assertion=callback_negative_control,
            )
        )

    already_told_variants = ["I already told you", "I also already told you that too", "you keep asking the same thing", "you are not listening"]
    for idx, phrase in enumerate(already_told_variants):
        records.append(
            make_record(
                group="D_routesignal_impact_already_told_loop",
                scenario=f"routesignal_already_told_full_capture_{idx:02d}",
                campaign=ROUTESIGNAL,
                turns=[
                    "__agent_open__",
                    "sure sure",
                    "callbacks are a problem",
                    "they cause delays",
                    "tomorrow at 3 works",
                    phrase,
                ],
                assertion=already_told_answer,
            )
        )

    appointment_sequences = [
        ["do you want to set an appointment with us", "that wasn't my question"],
        ["are you trying to book a review", "that was not my question"],
        ["so what now", "that wasn't my question"],
        ["is this an appointment request", "that was not my question"],
    ]
    for idx, tail in enumerate(appointment_sequences):
        records.append(
            make_record(
                group="E_appointment_next_step_question",
                scenario=f"routesignal_appointment_question_{idx:02d}",
                campaign=ROUTESIGNAL,
                turns=[
                    "__agent_open__",
                    "yes make it quick",
                    "call bags are a problem",
                    "I mean it causes delays",
                    "okay what now",
                    *tail,
                ],
                assertion=appointment_answer,
            )
        )

    stop_variants = ["bro stop", "bruh stop", "bra stop", "stop", "stop talking", "please stop"]
    for idx, phrase in enumerate(stop_variants):
        records.append(
            make_record(
                group="F_stop_asr_variants",
                scenario=f"routesignal_stop_variant_{idx:02d}",
                campaign=ROUTESIGNAL,
                turns=["__agent_open__", phrase],
                assertion=stop_answer,
            )
        )

    for idx, phrase in enumerate(["bus stop is near the office", "we use a stop gap process"]):
        records.append(
            make_record(
                group="F_stop_negative_controls",
                scenario=f"routesignal_stop_negative_control_{idx:02d}",
                campaign=ROUTESIGNAL,
                turns=["__agent_open__", phrase],
                assertion=stop_negative,
            )
        )

    telecom_sequences = [
        [
            "__agent_open__",
            "before we do anything how much is your product",
            "yeah last company wasted my time",
            "a little bit",
            "a bit of both",
            "I already told you yes",
            "mostly causing delays for us",
            "how about plan fit and coverage",
            "yeah that will be good",
            "before we go into that what is your product offer that we don't already have or current provider wouldn't provide for us how do I know the difference",
        ],
        ["__agent_open__", "what do you sell", "how do I know the difference from my current provider"],
        ["__agent_open__", "what is your product offer", "what would your specialist compare"],
        ["__agent_open__", "how much is your product", "what about plan fit and coverage", "yeah that will be good"],
        ["__agent_open__", "before anything what is your product", "yeah that will be good"],
        ["__agent_open__", "what makes you different", "how about plan fit and coverage"],
    ]
    telecom_assertions = [
        telecom_product_difference,
        telecom_product_difference,
        telecom_review_scope,
        telecom_review_acceptance,
        telecom_review_acceptance,
        telecom_review_scope,
    ]
    for idx, turns in enumerate(telecom_sequences):
        records.append(
            make_record(
                group="G_telecom_price_value_product_difference",
                scenario=f"telecom_product_difference_{idx:02d}",
                campaign=TELECOM,
                turns=turns,
                assertion=telecom_assertions[idx],
            )
        )

    product_question_variants = [
        "what do you sell",
        "what are you selling",
        "what is this product",
        "what exactly do you do",
        "what are you calling about",
        "what is your product offer",
    ]
    for campaign in (ROUTESIGNAL, TELECOM, INSURANCE):
        for idx, phrase in enumerate(product_question_variants):
            assertion: Callable[[dict[str, Any], list[str]], None]
            if campaign is ROUTESIGNAL:
                assertion = route_signal_product_answer
            else:
                assertion = lambda packet, failures, label=campaign["id"]: generic_product_answer(packet, failures, label)
            records.append(
                make_record(
                    group="H_campaign_offer_scope_product_questions",
                    scenario=f"{campaign['id']}_offer_question_{idx:02d}",
                    campaign=campaign,
                    turns=["__agent_open__", phrase],
                    assertion=assertion,
                )
            )

    for campaign in (ROUTESIGNAL, TELECOM, INSURANCE):
        for idx, phrase in enumerate(["why do I need a human review", "what will they do that you can't", "why can't you just tell me"]):
            records.append(
                make_record(
                    group="H_campaign_offer_scope_human_review",
                    scenario=f"{campaign['id']}_human_review_{idx:02d}",
                    campaign=campaign,
                    turns=["__agent_open__", "what do you sell", phrase],
                    assertion=human_review_answer,
                )
            )

    value_variants = ["what makes you different", "why should I care", "what problem do you solve", "is this worth my time"]
    for campaign in (ROUTESIGNAL, TELECOM, INSURANCE):
        for idx, phrase in enumerate(value_variants):
            records.append(
                make_record(
                    group="H_campaign_offer_scope_value_questions",
                    scenario=f"{campaign['id']}_value_question_{idx:02d}",
                    campaign=campaign,
                    turns=["__agent_open__", phrase],
                    assertion=lambda packet, failures, label=campaign["id"]: generic_value_answer(packet, failures, label)
                    if campaign is not ROUTESIGNAL
                    else route_signal_product_answer,
                )
            )

    records.extend(offer_scope_config_records())
    return records


def write_offer_scope_outputs(records: list[dict[str, Any]]) -> dict[str, Any]:
    offer_records = [record for record in records if record["group"].startswith("H_campaign_offer_scope")]
    failure_count = sum(1 for record in offer_records if not record["passed"])
    result = {
        "checkpoint_id": OFFER_SCOPE_CHECKPOINT_ID,
        "generated_at": utc_now(),
        "status": "pass" if failure_count == 0 else "fail",
        "matrix_size": len(offer_records),
        "pass_count": len(offer_records) - failure_count,
        "failure_count": failure_count,
        "required_offer_fields": list(REQUIRED_OFFER_FIELDS),
        "records": offer_records,
        "side_effects": {key: False for key in SIDE_EFFECT_KEYS},
    }
    OFFER_SCOPE_OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OFFER_SCOPE_OUT_DIR / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        f"# {OFFER_SCOPE_CHECKPOINT_ID}",
        "",
        "## Summary",
        f"- Status: `{result['status']}`",
        f"- Matrix size: `{result['matrix_size']}`",
        f"- Pass count: `{result['pass_count']}`",
        f"- Failure count: `{result['failure_count']}`",
        "",
        "## Required Offer Fields",
        *(f"- `{field}`" for field in REQUIRED_OFFER_FIELDS),
        "",
        "## Scenario Results",
    ]
    for record in offer_records:
        lines.extend(
            [
                f"### {record['scenario']}",
                f"- Passed: `{str(record['passed']).lower()}`",
                f"- Campaign: `{record['campaign_id']}`",
                f"- Buyer move: `{record.get('packet', {}).get('buyer_move_id')}`",
                f"- Response: {record.get('packet', {}).get('response', '')}",
            ]
        )
        if record["failures"]:
            lines.append(f"- Failures: `{'; '.join(record['failures'])}`")
        lines.append("")
    (OFFER_SCOPE_OUT_DIR / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


def write_outputs(records: list[dict[str, Any]]) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    failure_count = sum(1 for record in records if not record["passed"])
    group_counts = Counter(record["group"] for record in records)
    group_failures = Counter(record["group"] for record in records if not record["passed"])
    multi_turn_count = sum(1 for record in records if record["multi_turn"])
    side_effects = {key: False for key in SIDE_EFFECT_KEYS}
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "generated_at": utc_now(),
        "status": "pass" if failure_count == 0 and len(records) >= 80 and multi_turn_count >= 40 else "fail",
        "matrix_size": len(records),
        "multi_turn_scenario_count": multi_turn_count,
        "pass_count": len(records) - failure_count,
        "failure_count": failure_count,
        "group_counts": dict(sorted(group_counts.items())),
        "group_failure_counts": dict(sorted(group_failures.items())),
        "meets_minimum_matrix_size": len(records) >= 80,
        "meets_minimum_multi_turn_count": multi_turn_count >= 40,
        "records": records,
        "side_effects": side_effects,
    }
    offer_result = write_offer_scope_outputs(records)
    result["offer_scope_model_result"] = {
        "checkpoint_id": offer_result["checkpoint_id"],
        "status": offer_result["status"],
        "matrix_size": offer_result["matrix_size"],
        "failure_count": offer_result["failure_count"],
    }
    (OUT_DIR / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        f"# {CHECKPOINT_ID}",
        "",
        "## Summary",
        f"- Status: `{result['status']}`",
        f"- Matrix size: `{result['matrix_size']}`",
        f"- Multi-turn scenarios: `{result['multi_turn_scenario_count']}`",
        f"- Pass count: `{result['pass_count']}`",
        f"- Failure count: `{result['failure_count']}`",
        f"- Provider/LLM/CRM/email/calendar side effects: `false`",
        "",
        "## Group Counts",
        *(f"- `{group}`: `{count}`" for group, count in result["group_counts"].items()),
        "",
        "## Group Failure Counts",
        *(f"- `{group}`: `{count}`" for group, count in result["group_failure_counts"].items()),
        "",
        "## Scenario Results",
    ]
    for record in records:
        lines.extend(
            [
                f"### {record['scenario']}",
                f"- Group: `{record['group']}`",
                f"- Campaign: `{record['campaign_id']}`",
                f"- Passed: `{str(record['passed']).lower()}`",
                f"- Buyer move: `{record.get('packet', {}).get('buyer_move_id')}`",
                f"- Source: `{record.get('packet', {}).get('selected_action_source')}`",
                f"- Call control: `{record.get('packet', {}).get('call_control')}`",
                f"- Response: {record.get('packet', {}).get('response', '')}",
            ]
        )
        if record["failures"]:
            lines.append(f"- Failures: `{'; '.join(record['failures'])}`")
        lines.append("")
    (OUT_DIR / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


def main() -> None:
    records = run_matrix()
    result = write_outputs(records)
    print(
        json.dumps(
            {
                "checkpoint_id": result["checkpoint_id"],
                "status": result["status"],
                "matrix_size": result["matrix_size"],
                "multi_turn_scenario_count": result["multi_turn_scenario_count"],
                "pass_count": result["pass_count"],
                "failure_count": result["failure_count"],
                "group_failure_counts": result["group_failure_counts"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    if result["status"] != "pass":
        sys.exit(1)


if __name__ == "__main__":
    main()
