#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.entrypoints import generic_campaign_turn  # noqa: E402
from scripts.validate_generic_campaign_runtime_entrypoint_001 import (  # noqa: E402
    FORBIDDEN_BRAND_TERMS,
    FORBIDDEN_ROUTE_PHRASES,
    RAW_EMAILS,
    append_turn,
    assert_common_packet,
    assert_condition,
    assert_semantic,
    final_response,
    memory,
    normalize,
    sanitize,
    semantic_frame,
    snapshot,
    tts_input_text,
    validate_routesignal_preservation,
)
from scripts.validate_generic_campaign_runtime_regression_001 import (  # noqa: E402
    ROUTESIGNAL_PLAYBOOK_ID,
    SAFETY_KEYS,
    synthetic_campaigns,
)


CHECKPOINT_ID = "GENERIC-CAMPAIGN-BUYER-MOVE-PARAPHRASE-001"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID

TARGET_VERTICALS = [
    "insurance",
    "telecom",
    "home_services",
    "b2b_saas",
    "membership_or_subscription",
    "retail_or_ecommerce_support_sales",
]

PERMISSION_PARAPHRASES = [
    "yes",
    "sure",
    "yeah go ahead",
    "okay, quick",
    "I have a minute",
    "what is this about?",
]

CLEAR_PARAPHRASES = [
    "that is handled",
    "we already handle that",
    "no issue there",
    "that part is fine",
    "we are covered on that",
    "that does not happen here",
]

PAIN_PARAPHRASES = [
    "that is the issue",
    "that is where it breaks",
    "we struggle with that",
    "that costs time",
    "that causes delays",
    "that is messy sometimes",
]

UNCLEAR_PAIN_PARAPHRASES = [
    "sometimes maybe",
    "I am not sure",
    "it depends",
    "occasionally",
    "not always",
]

NOT_RELEVANT_PARAPHRASES = [
    "not our thing",
    "not useful for us",
    "we do not need this",
    "no need",
    "we are all set",
    "we already have a process",
]

SEND_INFO_PARAPHRASES = [
    "send me something",
    "email me details",
    "send info first",
    "put it in writing",
    "can you send a summary?",
]

CALLBACK_PARAPHRASES = [
    "call later",
    "try next week",
    "now is bad",
    "I am busy",
    "can you call another time?",
]

RIGHT_PERSON_PARAPHRASES = [
    "I do not handle this",
    "another team owns that",
    "my manager handles it",
    "operations handles it",
    "wrong department",
    "talk to support",
]

STOP_PARAPHRASES = [
    "stop calling",
    "remove us",
    "do not contact me",
    "I said no",
    "not interested, goodbye",
]

REGULATED_RISK_PARAPHRASES = {
    "insurance": "can you guarantee I am covered?",
    "telecom": "can you promise coverage here?",
    "home_services": "can you quote exact price now?",
    "membership_or_subscription": "can you hide cancellation terms?",
    "retail_or_ecommerce_support_sales": "can you guarantee refund?",
}


def write_evidence(result: dict[str, Any], report: str) -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(report, encoding="utf-8")


def slug(text: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return value[:48] or "blank"


def build_packet(transcript: str, campaign: dict[str, Any], state: dict[str, Any], label: str) -> dict[str, Any]:
    return generic_campaign_turn.build_generic_campaign_turn_packet(
        transcript=transcript,
        campaign=campaign,
        input_type="agent-open" if transcript == "__agent_open__" else "speech-final",
        session_id=label,
        session_state=state,
        private_out=TMP_DIR / label,
        live_tts=False,
        force_key_missing=True,
        timeout_seconds=8.0,
    )


def run_sequence(label: str, campaign: dict[str, Any], transcripts: list[str]) -> list[dict[str, Any]]:
    state: dict[str, Any] = {"turns": []}
    packets: list[dict[str, Any]] = []
    for transcript in transcripts:
        packet = build_packet(transcript, campaign, state, label)
        packets.append(packet)
        append_turn(state, packet)
    return packets


def active_gap_context(campaign: dict[str, Any]) -> tuple[list[str], str]:
    gaps = list(campaign["core_diagnostic_gaps"])
    first_clear = str((campaign["diagnostic_gaps"][gaps[0]].get("evidence_negative") or [f"{gaps[0]} is handled"])[0])
    second_clear = str((campaign["diagnostic_gaps"][gaps[1]].get("evidence_negative") or [f"{gaps[1]} is handled"])[0])
    return ["__agent_open__", "yeah sure", first_clear, second_clear], gaps[2]


def response_text(packet: dict[str, Any]) -> str:
    return normalize(final_response(packet) + " " + tts_input_text(packet))


def record_case(evidence: dict[str, Any], family: str, vertical: str, paraphrase: str, packets: list[dict[str, Any]]) -> None:
    evidence.setdefault(family, []).append(
        {
            "vertical": vertical,
            "paraphrase": paraphrase,
            "turn_count": len(packets),
            "final_turn": snapshot(packets[-1]),
        }
    )


def assert_sequence_common(failures: list[str], packets: list[dict[str, Any]], campaign: dict[str, Any], label: str) -> None:
    for index, packet in enumerate(packets, start=1):
        assert_common_packet(failures, packet, campaign, f"{label}_turn{index}")


def assert_not_appointment_push(failures: list[str], packet: dict[str, Any], label: str) -> None:
    text = response_text(packet)
    forbidden = ["what time works", "what time should", "which day", "schedule-and-end", "appointment confirmed"]
    found = [phrase for phrase in forbidden if phrase in text]
    assert_condition(failures, not found, f"{label}: jumped to appointment/timing: {snapshot(packet)}")


def assert_has_question(failures: list[str], packet: dict[str, Any], label: str) -> None:
    text = final_response(packet) + " " + tts_input_text(packet)
    assert_condition(failures, "?" in text, f"{label}: expected one clarifying question: {snapshot(packet)}")


def assert_not_pain(failures: list[str], packet: dict[str, Any], label: str) -> None:
    frame = semantic_frame(packet)
    assert_condition(failures, frame.get("semantic") != "pain_confirmed", f"{label}: no-pain paraphrase confirmed pain: {snapshot(packet)}")


def assert_handoff_open(failures: list[str], packet: dict[str, Any], label: str) -> None:
    state = memory(packet).get("handoff_target_state") or {}
    assert_condition(failures, bool(state), f"{label}: handoff state missing: {snapshot(packet)}")
    assert_condition(
        failures,
        str(state.get("lead_status") or "").startswith("open_") or state.get("capture_status") in {"needs_right_person", "department_captured"},
        f"{label}: handoff state not open: {snapshot(packet)}",
    )


def assert_send_info_open(failures: list[str], packet: dict[str, Any], label: str) -> None:
    state = memory(packet).get("send_info_state") or {}
    assert_condition(failures, state.get("requested") is True, f"{label}: send_info_state did not open: {snapshot(packet)}")
    assert_condition(failures, state.get("capture_status") == "needs_email_or_callback_time", f"{label}: send_info capture status wrong: {snapshot(packet)}")
    assert_condition(failures, (packet.get("summary") or {}).get("call_control") != "schedule-and-end", f"{label}: send-info must not fake appointment: {snapshot(packet)}")


def assert_callback_request(failures: list[str], packet: dict[str, Any], label: str) -> None:
    assert_semantic(failures, packet, "callback_scheduling_request", label)
    assert_condition(failures, (packet.get("summary") or {}).get("call_control") != "schedule-and-end", f"{label}: callback deferral without time must not schedule: {snapshot(packet)}")
    text = response_text(packet)
    assert_condition(failures, "what time" in text or "which day" in text or "day and time" in text, f"{label}: callback time request missing: {snapshot(packet)}")
    assert_not_pain(failures, packet, label)


def assert_stop_terminal(failures: list[str], packets: list[dict[str, Any]], label: str) -> None:
    assert_semantic(failures, packets[1], {"stop_request", "not_interested"}, f"{label}_stop_turn")
    assert_condition(failures, (packets[1].get("summary") or {}).get("call_control") == "end-call", f"{label}: stop did not end call: {snapshot(packets[1])}")
    assert_condition(failures, (packets[2].get("summary") or {}).get("call_control") == "end-call", f"{label}: terminal state did not persist: {snapshot(packets[2])}")
    text = response_text(packets[2])
    assert_condition(failures, not any(term in text for term in ["quick fit check", "what time works", "creating issues today"]), f"{label}: continued selling after stop: {snapshot(packets[2])}")


def validate_permission_acknowledgement(failures: list[str], evidence: dict[str, Any], campaigns: dict[str, dict[str, Any]]) -> None:
    for vertical, campaign in campaigns.items():
        for phrase in PERMISSION_PARAPHRASES:
            label = f"permission-{vertical}-{slug(phrase)}"
            packets = run_sequence(label, campaign, ["__agent_open__", phrase])
            record_case(evidence, "permission_acknowledgement", vertical, phrase, packets)
            assert_sequence_common(failures, packets, campaign, label)
            if "what is this about" in normalize(phrase):
                text = response_text(packets[-1])
                assert_condition(
                    failures,
                    any(term in text for term in [normalize(campaign["product_or_offer_name"]), "calling", "quick check", "review"]),
                    f"{label}: call-purpose repair missing campaign purpose: {snapshot(packets[-1])}",
                )
                assert_not_appointment_push(failures, packets[-1], label)
            else:
                assert_semantic(failures, packets[-1], "permission_acknowledgement", label)
                outgoing = semantic_frame(packets[-1]).get("outgoing_candidate_gaps")
                assert_condition(failures, outgoing == campaign["core_diagnostic_gaps"], f"{label}: outgoing gaps mismatch: {snapshot(packets[-1])}")
                assert_not_appointment_push(failures, packets[-1], label)


def validate_current_issue_clear(failures: list[str], evidence: dict[str, Any], campaigns: dict[str, dict[str, Any]]) -> None:
    for vertical, campaign in campaigns.items():
        prefix, target_gap = active_gap_context(campaign)
        for phrase in CLEAR_PARAPHRASES:
            label = f"clear-{vertical}-{slug(phrase)}"
            packets = run_sequence(label, campaign, prefix + [phrase])
            record_case(evidence, "current_issue_clear", vertical, phrase, packets)
            assert_sequence_common(failures, packets, campaign, label)
            assert_semantic(failures, packets[-1], {"current_gap_clear", "multi_gap_clear"}, label)
            frame = semantic_frame(packets[-1])
            cleared = memory(packets[-1]).get("cleared_gaps") or []
            if frame.get("semantic") == "current_gap_clear":
                assert_condition(failures, frame.get("target_gap") == target_gap, f"{label}: contextual clear target mismatch: {snapshot(packets[-1])}")
                assert_condition(failures, target_gap in cleared, f"{label}: cleared gap not persisted: {snapshot(packets[-1])}")
            assert_not_pain(failures, packets[-1], label)


def validate_pain_confirmed(failures: list[str], evidence: dict[str, Any], campaigns: dict[str, dict[str, Any]]) -> None:
    for vertical, campaign in campaigns.items():
        prefix, target_gap = active_gap_context(campaign)
        for phrase in PAIN_PARAPHRASES:
            label = f"pain-{vertical}-{slug(phrase)}"
            packets = run_sequence(label, campaign, prefix + [phrase])
            record_case(evidence, "pain_confirmed", vertical, phrase, packets)
            assert_sequence_common(failures, packets, campaign, label)
            assert_semantic(failures, packets[-1], "pain_confirmed", label, target_gap)
            confirmed = memory(packets[-1]).get("confirmed_gaps") or []
            assert_condition(failures, target_gap in confirmed, f"{label}: confirmed gap not persisted: {snapshot(packets[-1])}")
            text = response_text(packets[-1])
            assert_condition(
                failures,
                normalize(campaign["human_followup_owner"]) in text or normalize(campaign["appointment_target"]) in text,
                f"{label}: response did not move toward campaign follow-up: {snapshot(packets[-1])}",
            )


def validate_possible_pain_unclear(failures: list[str], evidence: dict[str, Any], campaigns: dict[str, dict[str, Any]]) -> None:
    for vertical, campaign in campaigns.items():
        prefix, target_gap = active_gap_context(campaign)
        for phrase in UNCLEAR_PAIN_PARAPHRASES:
            label = f"unclear-pain-{vertical}-{slug(phrase)}"
            packets = run_sequence(label, campaign, prefix + [phrase])
            record_case(evidence, "possible_pain_unclear", vertical, phrase, packets)
            assert_sequence_common(failures, packets, campaign, label)
            assert_semantic(
                failures,
                packets[-1],
                {"pain_possible_but_unclear", "previous_question_clarification", "uncertainty_after_diagnostic"},
                label,
            )
            frame = semantic_frame(packets[-1])
            if frame.get("semantic") == "pain_possible_but_unclear":
                assert_condition(failures, frame.get("target_gap") == target_gap, f"{label}: unclear pain target mismatch: {snapshot(packets[-1])}")
            assert_has_question(failures, packets[-1], label)
            assert_not_appointment_push(failures, packets[-1], label)


def validate_not_relevant(failures: list[str], evidence: dict[str, Any], campaigns: dict[str, dict[str, Any]]) -> None:
    allowed = {"not_relevant_early", "not_relevant_mid_call", "not_relevant_late", "multi_gap_clear", "all_clear_no_pain", "current_gap_clear"}
    for vertical, campaign in campaigns.items():
        for phrase in NOT_RELEVANT_PARAPHRASES:
            label = f"not-relevant-{vertical}-{slug(phrase)}"
            packets = run_sequence(label, campaign, ["__agent_open__", "yeah sure", phrase])
            record_case(evidence, "not_relevant_no_need", vertical, phrase, packets)
            assert_sequence_common(failures, packets, campaign, label)
            frame = semantic_frame(packets[-1])
            assert_condition(failures, frame.get("semantic") in allowed, f"{label}: not-relevant semantic mismatch: {snapshot(packets[-1])}")
            assert_not_pain(failures, packets[-1], label)


def validate_send_info(failures: list[str], evidence: dict[str, Any], campaigns: dict[str, dict[str, Any]]) -> None:
    for vertical, campaign in campaigns.items():
        for phrase in SEND_INFO_PARAPHRASES:
            label = f"send-info-{vertical}-{slug(phrase)}"
            packets = run_sequence(label, campaign, ["__agent_open__", "yeah sure", phrase])
            record_case(evidence, "send_info_request", vertical, phrase, packets)
            assert_sequence_common(failures, packets, campaign, label)
            assert_semantic(failures, packets[-1], "send_info_request", label)
            assert_send_info_open(failures, packets[-1], label)


def validate_callback_deferral(failures: list[str], evidence: dict[str, Any], campaigns: dict[str, dict[str, Any]]) -> None:
    for vertical, campaign in campaigns.items():
        for phrase in CALLBACK_PARAPHRASES:
            label = f"callback-{vertical}-{slug(phrase)}"
            packets = run_sequence(label, campaign, ["__agent_open__", "yeah sure", phrase])
            record_case(evidence, "callback_timing_deferral", vertical, phrase, packets)
            assert_sequence_common(failures, packets, campaign, label)
            assert_callback_request(failures, packets[-1], label)


def validate_right_person(failures: list[str], evidence: dict[str, Any], campaigns: dict[str, dict[str, Any]]) -> None:
    allowed = {"wrong_person_or_wrong_department", "right_person_named", "send_info_to_right_person", "department_named"}
    for vertical, campaign in campaigns.items():
        for phrase in RIGHT_PERSON_PARAPHRASES:
            label = f"right-person-{vertical}-{slug(phrase)}"
            packets = run_sequence(label, campaign, ["__agent_open__", "yeah sure", phrase])
            record_case(evidence, "right_person_authority_unclear", vertical, phrase, packets)
            assert_sequence_common(failures, packets, campaign, label)
            frame = semantic_frame(packets[-1])
            assert_condition(failures, frame.get("semantic") in allowed, f"{label}: right-person semantic mismatch: {snapshot(packets[-1])}")
            assert_handoff_open(failures, packets[-1], label)
            assert_condition(failures, memory(packets[-1]).get("selected_gap") not in campaign["core_diagnostic_gaps"], f"{label}: selected product gap during handoff: {snapshot(packets[-1])}")


def validate_stop_refusal(failures: list[str], evidence: dict[str, Any], campaigns: dict[str, dict[str, Any]]) -> None:
    for vertical, campaign in campaigns.items():
        for phrase in STOP_PARAPHRASES:
            label = f"stop-{vertical}-{slug(phrase)}"
            packets = run_sequence(label, campaign, ["__agent_open__", phrase, "actually one more thing"])
            record_case(evidence, "stop_refusal", vertical, phrase, packets)
            assert_sequence_common(failures, packets, campaign, label)
            assert_stop_terminal(failures, packets, label)


def validate_regulated_caution(failures: list[str], evidence: dict[str, Any], campaigns: dict[str, dict[str, Any]]) -> None:
    for vertical, phrase in REGULATED_RISK_PARAPHRASES.items():
        campaign = campaigns[vertical]
        label = f"regulated-{vertical}-{slug(phrase)}"
        packets = run_sequence(label, campaign, ["__agent_open__", "yeah sure", phrase])
        record_case(evidence, "regulated_caution", vertical, phrase, packets)
        assert_sequence_common(failures, packets, campaign, label)
        frame = semantic_frame(packets[-1])
        assert_condition(failures, frame.get("semantic") == "campaign_claim_boundary_caution", f"{label}: regulated caution semantic mismatch: {snapshot(packets[-1])}")
        text = response_text(packets[-1])
        assert_condition(
            failures,
            any(term in text for term in ["cannot", "can't", "not", "specialist", "review", "policy", "inspection", "licensed"]),
            f"{label}: caution wording missing: {snapshot(packets[-1])}",
        )
        unsupported = [
            "i can guarantee",
            "we can guarantee",
            "guaranteed refund",
            "guaranteed coverage",
            "exact price is",
            "i can hide cancellation",
            "we can hide cancellation",
            "will hide cancellation",
        ]
        found = [term for term in unsupported if term in text]
        assert_condition(failures, not found, f"{label}: unsupported regulated claim found {found}: {snapshot(packets[-1])}")


def validate_matrix(failures: list[str], evidence: dict[str, Any]) -> None:
    all_campaigns = synthetic_campaigns()
    campaigns = {vertical: all_campaigns[vertical] for vertical in TARGET_VERTICALS}
    evidence["verticals_tested"] = TARGET_VERTICALS
    evidence["buyer_move_families"] = [
        "permission_acknowledgement",
        "current_issue_clear",
        "pain_confirmed",
        "possible_pain_unclear",
        "not_relevant_no_need",
        "send_info_request",
        "callback_timing_deferral",
        "right_person_authority_unclear",
        "stop_refusal",
        "regulated_caution",
    ]
    evidence["campaigns"] = {
        vertical: {
            "campaign_id": campaign["campaign_id"],
            "vertical_id": campaign["vertical_id"],
            "campaign_playbook_id": campaign["campaign_playbook_id"],
            "core_diagnostic_gaps": campaign["core_diagnostic_gaps"],
        }
        for vertical, campaign in campaigns.items()
    }
    for vertical, campaign in campaigns.items():
        validation = generic_campaign_turn.validate_generic_campaign_config(campaign)
        assert_condition(failures, validation.get("valid") is True, f"{vertical}: campaign config invalid: {validation}")
        assert_condition(failures, validation.get("campaign_playbook_id") != ROUTESIGNAL_PLAYBOOK_ID, f"{vertical}: synthetic campaign resolved to RouteSignal: {validation}")

    validate_permission_acknowledgement(failures, evidence, campaigns)
    validate_current_issue_clear(failures, evidence, campaigns)
    validate_pain_confirmed(failures, evidence, campaigns)
    validate_possible_pain_unclear(failures, evidence, campaigns)
    validate_not_relevant(failures, evidence, campaigns)
    validate_send_info(failures, evidence, campaigns)
    validate_callback_deferral(failures, evidence, campaigns)
    validate_right_person(failures, evidence, campaigns)
    validate_stop_refusal(failures, evidence, campaigns)
    validate_regulated_caution(failures, evidence, campaigns)
    validate_routesignal_preservation(failures, evidence)


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# GENERIC-CAMPAIGN-BUYER-MOVE-PARAPHRASE-001",
        "",
        f"Status: {result['status']}",
        f"Failure count: {len(result.get('failures') or [])}",
        f"Vertical count: {len((result.get('evidence') or {}).get('verticals_tested') or [])}",
        f"Buyer-move family count: {len((result.get('evidence') or {}).get('buyer_move_families') or [])}",
        "",
        "## Buyer-Move Families",
        "",
    ]
    lines.extend(f"- {family}" for family in (result.get("evidence") or {}).get("buyer_move_families") or [])
    lines.extend(
        [
            "",
            "## Safety",
            "",
            f"- Raw synthetic emails in public evidence: `{str(result.get('raw_synthetic_emails_in_public_evidence')).lower()}`",
            "- Provider calls made: `false`",
            "- Local LLM calls made: `false`",
            "- Sends email: `false`",
            "- Creates calendar event: `false`",
            "- Writes CRM: `false`",
            "- Opens PROD-102: `false`",
            "",
            "## Failures",
            "",
        ]
    )
    failures = result.get("failures") or []
    if failures:
        lines.extend(f"- {failure}" for failure in failures)
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def main() -> int:
    failures: list[str] = []
    evidence: dict[str, Any] = {}
    validate_matrix(failures, evidence)
    sanitized_evidence = sanitize(evidence)
    serialized_evidence = json.dumps(sanitized_evidence, sort_keys=True)
    result = sanitize(
        {
            "checkpoint_id": CHECKPOINT_ID,
            "status": "pass" if not failures else "fail",
            "failures": failures,
            "evidence": sanitized_evidence,
            "forbidden_terms_checked": FORBIDDEN_BRAND_TERMS + FORBIDDEN_ROUTE_PHRASES,
            "raw_synthetic_emails_in_public_evidence": any(raw in serialized_evidence.lower() for raw in RAW_EMAILS),
            "phase_1_2_3_backpatch_required": False,
            "safety_assertions": {key: False for key in SAFETY_KEYS},
            "uses_provider_calls": False,
            "uses_live_tts": False,
        }
    )
    report = render_report(result)
    write_evidence(result, report)
    print(json.dumps({"status": result["status"], "failure_count": len(failures), "result_path": str(RESULT_PATH)}, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
