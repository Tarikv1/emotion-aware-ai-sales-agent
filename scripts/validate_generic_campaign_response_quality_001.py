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
    RAW_EMAILS,
    append_turn,
    assert_condition,
    final_response,
    sanitize,
    semantic_frame,
    snapshot,
    validate_routesignal_preservation,
)
from scripts.validate_generic_campaign_runtime_regression_001 import synthetic_campaigns  # noqa: E402


CHECKPOINT_ID = "GENERIC-CAMPAIGN-RESPONSE-QUALITY-001"
GENERATED_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = GENERATED_DIR / "result.json"
REPORT_PATH = GENERATED_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID

ROUTESIGNAL_PLAYBOOK_ID = "ROUTESIGNAL-DIAGNOSTIC-PLAYBOOK-001"
TARGET_VERTICALS = [
    "b2b_saas",
    "insurance",
    "telecom",
    "home_services",
    "healthcare_admin_or_medical_equipment",
    "automotive_service",
    "membership_or_subscription",
    "retail_or_ecommerce_support_sales",
]
FORBIDDEN_TERMS = [
    "RouteSignal",
    "Northstar",
    "Starter",
    "Growth",
    "$29",
    "$59",
    "inbound demo",
    "demo follow-up",
    "missed callbacks",
    "manual tracking",
    "messy handoffs",
]
INTERNAL_TERMS = [
    "semantic",
    "playbook",
    "gap id",
    "campaign config",
    "guardrail",
    "runtime",
]
SAFETY_KEYS = [
    "provider_calls_made",
    "local_llm_calls_made",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
]
PAIN_PHRASES = {
    "b2b_saas": "visibility is the problem",
    "insurance": "premium is a problem",
    "telecom": "coverage is the issue",
    "home_services": "estimate is unclear",
    "healthcare_admin_or_medical_equipment": "specialist review is needed",
    "automotive_service": "warranty estimate is the problem",
    "membership_or_subscription": "renewal is the issue",
    "retail_or_ecommerce_support_sales": "return policy is the concern",
}
RISKY_QUESTIONS = {
    "b2b_saas": "can you guarantee integration security?",
    "insurance": "can you guarantee I am covered?",
    "telecom": "can you promise coverage here?",
    "home_services": "can you quote exact price now?",
    "healthcare_admin_or_medical_equipment": "can you guarantee this equipment solves the issue?",
    "automotive_service": "can you guarantee repair cost?",
    "membership_or_subscription": "can you hide cancellation terms?",
    "retail_or_ecommerce_support_sales": "can you guarantee refund?",
}
FALLBACK_REPAIR_TURNS = [
    "__agent_open__",
    "yeah sure",
    "what is this about?",
    "I don't understand",
    "what does this include?",
    "what happens next?",
    "is it expensive?",
    "can you help with my password?",
]
QUALITY_FAILURES_BEFORE_PATCH = {
    "red_run_failure_count": 152,
    "clusters": [
        "Generic openings used four sentences and awkward 'with <owner> would be useful' phrasing.",
        "Permission diagnostics used clunky 'creating issues today' wording.",
        "Pain-confirmed bridges used five sentences and unnatural 'short review with <owner>' wording.",
        "Fallback repair reused robotic 'safe check' / if-X-matters text and repeated prior price sentences.",
    ],
}
PATCHES_MADE = [
    "Compressed generic openings to two sentences while preserving caller, offer, reason, and permission ask.",
    "Added generic owner article helpers so role phrases read as 'a specialist' or 'an implementation specialist'.",
    "Reworded generic diagnostic, next-step, product-detail, price, and effort fallbacks to avoid clunky issue/matter phrasing.",
    "Shortened generic pain-confirmed bridges to a human appointment-setting form without changing the semantic route.",
    "Added a generic duplicate/fallback progression path that does not append repeated price sentences.",
]


def write_evidence(result: dict[str, Any], report: str) -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(report, encoding="utf-8")


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def sentence_count(text: str) -> int:
    return len([part for part in re.split(r"[.!?]+", str(text or "")) if part.strip()])


def tts_input_text(packet: dict[str, Any]) -> str:
    summary = packet.get("summary") or {}
    body = packet.get("packet") or {}
    tts = body.get("tts_delivery") or {}
    return str(summary.get("tts_input_text") or tts.get("tts_input_text") or "")


def provider_rendered_text(packet: dict[str, Any]) -> str:
    voice = ((packet.get("packet") or {}).get("voice_delivery") or {})
    rendering = voice.get("provider_rendering") or {}
    return str(rendering.get("rendered_text") or "")


def clean_for_meaning(text: str) -> str:
    value = re.sub(r"<break[^>]*>", " ", str(text or ""), flags=re.IGNORECASE)
    value = value.replace("I'm", "I am").replace("don't", "do not").replace("can't", "cannot")
    value = re.sub(r"\b(?:well|so|um|uh)\b[, ]*", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"[^a-zA-Z0-9$ ]+", " ", value)
    return re.sub(r"\s+", " ", value).strip().lower()


def token_set(text: str) -> set[str]:
    stop = {"a", "an", "and", "or", "the", "to", "for", "of", "in", "on", "it", "is", "am", "are", "be"}
    return {word for word in clean_for_meaning(text).split() if len(word) > 2 and word not in stop}


def forbidden_matches(text: str) -> list[str]:
    lowered = normalize(text)
    return [term for term in FORBIDDEN_TERMS if term.lower() in lowered]


def internal_matches(text: str) -> list[str]:
    lowered = normalize(text)
    return [term for term in INTERNAL_TERMS if term in lowered]


def raw_snake_case_terms(text: str) -> list[str]:
    return sorted(set(re.findall(r"\b[a-z][a-z0-9]+(?:_[a-z0-9]+)+\b", str(text or ""))))


def broken_punctuation(text: str) -> bool:
    return bool(re.search(r" {2,}|[.?!,]{2,}|\s+[.?!,]|[.?!,]\s+[.?!,]", str(text or "")))


def gap_label(campaign: dict[str, Any], gap_id: str) -> str:
    definition = (campaign.get("diagnostic_gaps") or {}).get(gap_id) or {}
    return str(definition.get("label") or gap_id).replace("_", " ").strip()


def first_gap_clear_phrase(campaign: dict[str, Any]) -> str:
    first_gap = list(campaign.get("core_diagnostic_gaps") or campaign.get("gap_order") or [])[0]
    definition = (campaign.get("diagnostic_gaps") or {}).get(first_gap) or {}
    negatives = list(definition.get("evidence_negative") or [])
    return str(negatives[0] if negatives else f"{gap_label(campaign, first_gap)} is handled")


def run_turn(campaign: dict[str, Any], transcript: str, state: dict[str, Any], session_id: str) -> dict[str, Any]:
    packet = generic_campaign_turn.build_generic_campaign_turn_packet(
        transcript=transcript,
        campaign=campaign,
        input_type="agent-open" if transcript == "__agent_open__" else "speech-final",
        session_id=session_id,
        session_state=state,
        private_out=TMP_DIR / session_id,
        live_tts=False,
        force_key_missing=True,
        timeout_seconds=8.0,
    )
    append_turn(state, packet)
    return packet


def run_sequence(campaign: dict[str, Any], sequence: list[str], session_id: str) -> list[dict[str, Any]]:
    state: dict[str, Any] = {"turns": []}
    packets: list[dict[str, Any]] = []
    for transcript in sequence:
        packets.append(run_turn(campaign, transcript, state, session_id))
    return packets


def assert_safety(failures: list[str], packet: dict[str, Any], label: str) -> None:
    for key in SAFETY_KEYS:
        assert_condition(failures, packet.get(key) is False, f"{label}: {key} must be false: {snapshot(packet)}")
    assert_condition(failures, packet.get("provider_agent_used") is False, f"{label}: provider_agent_used must be false")
    assert_condition(
        failures,
        packet.get("durable_provider_agent_created") is False,
        f"{label}: durable_provider_agent_created must be false",
    )
    assert_condition(failures, packet.get("voice_cloning_used") is False, f"{label}: voice_cloning_used must be false")


def assert_generic_playbook(failures: list[str], packet: dict[str, Any], label: str) -> None:
    playbook_id = str(packet.get("campaign_playbook_id") or "")
    assert_condition(
        failures,
        bool(playbook_id and playbook_id != ROUTESIGNAL_PLAYBOOK_ID),
        f"{label}: generic packet used RouteSignal/default playbook: {snapshot(packet)}",
    )


def assert_meaning_preserved(failures: list[str], packet: dict[str, Any], label: str) -> None:
    final = final_response(packet)
    tts = tts_input_text(packet)
    if not final or not tts:
        return
    final_tokens = token_set(final)
    tts_tokens = token_set(tts)
    if not final_tokens:
        return
    missing = final_tokens - tts_tokens
    overlap = 1.0 - (len(missing) / max(1, len(final_tokens)))
    assert_condition(
        failures,
        overlap >= 0.78,
        f"{label}: tts_input_text drifted from final_response; missing={sorted(missing)} final={final!r} tts={tts!r}",
    )


def assert_text_quality(
    failures: list[str],
    packet: dict[str, Any],
    campaign: dict[str, Any],
    label: str,
    *,
    regulated_caution: bool = False,
) -> None:
    assert_generic_playbook(failures, packet, label)
    assert_safety(failures, packet, label)
    text = final_response(packet)
    lowered = normalize(text)
    owner = normalize(str(campaign.get("human_followup_owner") or ""))
    for source_name, source_text in {
        "final_response": text,
        "tts_input_text": tts_input_text(packet),
        "provider_rendered_text": provider_rendered_text(packet),
    }.items():
        found = forbidden_matches(source_text)
        assert_condition(failures, not found, f"{label}: {source_name} leaked forbidden terms {found}: {sanitize(source_text)}")
    assert_condition(failures, not raw_snake_case_terms(text), f"{label}: raw snake_case term in final_response: {text!r}")
    assert_condition(failures, not broken_punctuation(text), f"{label}: broken punctuation or double spaces: {text!r}")
    assert_condition(failures, not internal_matches(text), f"{label}: internal runtime wording leaked: {text!r}")
    if owner:
        assert_condition(
            failures,
            f"with {owner}" not in lowered,
            f"{label}: unnatural 'with <owner>' phrase: {text!r}",
        )
    assert_condition(failures, "safe check" not in lowered, f"{label}: robotic safe-check wording: {text!r}")
    assert_condition(failures, "creating issues" not in lowered, f"{label}: clunky creating-issues wording: {text!r}")
    assert_condition(failures, "would be useful" not in lowered, f"{label}: awkward usefulness phrasing: {text!r}")
    assert_condition(failures, not re.search(r"\bif .{8,120}\bmatters?\b", lowered), f"{label}: robotic if-X-matters phrasing: {text!r}")
    max_sentences = 3 if regulated_caution else 2
    assert_condition(
        failures,
        sentence_count(text) <= max_sentences,
        f"{label}: response has too many sentences ({sentence_count(text)}): {text!r}",
    )
    assert_meaning_preserved(failures, packet, label)


def assert_no_repeated_sentence(failures: list[str], packets: list[dict[str, Any]], label: str) -> None:
    previous_sentences: set[str] = set()
    for index, packet in enumerate(packets, start=1):
        sentences = [normalize(item) for item in re.split(r"(?<=[.!?])\s+", final_response(packet)) if normalize(item)]
        repeated = [sentence for sentence in sentences if sentence in previous_sentences]
        assert_condition(failures, not repeated, f"{label}/turn-{index}: repeated sentence: {repeated}")
        previous_sentences.update(sentences)


def assert_no_appointment_ask(failures: list[str], packet: dict[str, Any], label: str) -> None:
    lowered = normalize(final_response(packet))
    forbidden = ["what time works", "what time should", "schedule", "book", "appointment confirmation"]
    assert_condition(failures, not any(item in lowered for item in forbidden), f"{label}: premature appointment ask: {snapshot(packet)}")


def validate_opening(failures: list[str], campaign: dict[str, Any], evidence: list[dict[str, Any]], vertical: str) -> None:
    packets = run_sequence(campaign, ["__agent_open__"], f"{CHECKPOINT_ID}-{vertical}-opening")
    packet = packets[-1]
    text = normalize(final_response(packet))
    assert_text_quality(failures, packet, campaign, f"{vertical}/opening")
    assert_condition(failures, normalize(str(campaign.get("client_name") or "")) in text, f"{vertical}/opening: missing client identity")
    assert_condition(failures, normalize(str(campaign.get("product_or_offer_name") or "")) in text, f"{vertical}/opening: missing offer reason")
    assert_condition(failures, "minute" in text or "quick" in text, f"{vertical}/opening: missing permission ask")
    record(evidence, vertical, "opening", packet)


def validate_permission(failures: list[str], campaign: dict[str, Any], evidence: list[dict[str, Any]], vertical: str) -> None:
    packets = run_sequence(campaign, ["__agent_open__", "yeah sure"], f"{CHECKPOINT_ID}-{vertical}-permission")
    packet = packets[-1]
    assert_text_quality(failures, packet, campaign, f"{vertical}/permission")
    assert_condition(failures, semantic_frame(packet).get("semantic") == "permission_acknowledgement", f"{vertical}/permission: wrong semantic")
    assert_condition(failures, final_response(packet).count("?") == 1, f"{vertical}/permission: should ask one concise question")
    assert_no_appointment_ask(failures, packet, f"{vertical}/permission")
    record(evidence, vertical, "permission_to_diagnostic", packet)


def validate_current_gap_clear(failures: list[str], campaign: dict[str, Any], evidence: list[dict[str, Any]], vertical: str) -> None:
    first_gap = list(campaign.get("core_diagnostic_gaps") or [])[0]
    sequence = ["__agent_open__", "yeah sure", first_gap_clear_phrase(campaign)]
    packets = run_sequence(campaign, sequence, f"{CHECKPOINT_ID}-{vertical}-current-gap-clear")
    packet = packets[-1]
    label = gap_label(campaign, first_gap)
    text = normalize(final_response(packet))
    assert_text_quality(failures, packet, campaign, f"{vertical}/current_gap_clear")
    assert_condition(failures, semantic_frame(packet).get("semantic") == "current_gap_clear", f"{vertical}/current_gap_clear: wrong semantic")
    assert_condition(failures, semantic_frame(packet).get("target_gap") == first_gap, f"{vertical}/current_gap_clear: wrong target gap")
    assert_condition(failures, text.count(normalize(label)) <= 1, f"{vertical}/current_gap_clear: repeated cleared gap: {final_response(packet)!r}")
    assert_condition(failures, "problem" not in text or "not a problem" in text, f"{vertical}/current_gap_clear: implied pain confirmation")
    record(evidence, vertical, "current_gap_clear", packet)


def validate_pain_confirmed(failures: list[str], campaign: dict[str, Any], evidence: list[dict[str, Any]], vertical: str) -> None:
    phrase = PAIN_PHRASES[vertical]
    packets = run_sequence(campaign, ["__agent_open__", "yeah sure", phrase], f"{CHECKPOINT_ID}-{vertical}-pain-confirmed")
    packet = packets[-1]
    text = normalize(final_response(packet))
    owner = normalize(str(campaign.get("human_followup_owner") or ""))
    target = normalize(str(campaign.get("appointment_target") or ""))
    assert_text_quality(failures, packet, campaign, f"{vertical}/pain_confirmed")
    assert_condition(failures, semantic_frame(packet).get("semantic") == "pain_confirmed", f"{vertical}/pain_confirmed: wrong semantic")
    assert_condition(
        failures,
        bool((owner and owner in text) or (target and target in text) or "review" in text),
        f"{vertical}/pain_confirmed: missing human follow-up bridge: {snapshot(packet)}",
    )
    assert_condition(
        failures,
        not any(term in text for term in ["buy now", "sign up", "purchase", "contract now"]),
        f"{vertical}/pain_confirmed: full-sale close wording: {snapshot(packet)}",
    )
    record(evidence, vertical, "pain_confirmed", packet)


def validate_send_info(failures: list[str], campaign: dict[str, Any], evidence: list[dict[str, Any]], vertical: str) -> None:
    packets = run_sequence(campaign, ["__agent_open__", "yeah sure", "send me details", "yes send it"], f"{CHECKPOINT_ID}-{vertical}-send-info")
    packet = packets[-1]
    text = normalize(final_response(packet))
    assert_text_quality(failures, packet, campaign, f"{vertical}/send_info")
    assert_condition(failures, "email" in text or "callback" in text, f"{vertical}/send_info: missing email/callback ask")
    assert_condition(failures, "sent" not in text and "scheduled" not in text, f"{vertical}/send_info: fake send or schedule")
    record(evidence, vertical, "send_info", packet)


def validate_right_person(failures: list[str], campaign: dict[str, Any], evidence: list[dict[str, Any]], vertical: str) -> None:
    packets = run_sequence(campaign, ["__agent_open__", "yeah sure", "I'm not the person", "operations handles that"], f"{CHECKPOINT_ID}-{vertical}-right-person")
    packet = packets[-1]
    text = normalize(final_response(packet))
    assert_text_quality(failures, packet, campaign, f"{vertical}/right_person")
    assert_condition(
        failures,
        any(term in text for term in ["right", "contact", "team", "person", "email", "callback", "stop"]),
        f"{vertical}/right_person: missing right-person path: {snapshot(packet)}",
    )
    record(evidence, vertical, "right_person_handoff", packet)


def validate_regulated_caution(failures: list[str], campaign: dict[str, Any], evidence: list[dict[str, Any]], vertical: str) -> None:
    packets = run_sequence(campaign, ["__agent_open__", "yeah sure", RISKY_QUESTIONS[vertical]], f"{CHECKPOINT_ID}-{vertical}-regulated-caution")
    packet = packets[-1]
    text = normalize(final_response(packet))
    assert_text_quality(failures, packet, campaign, f"{vertical}/regulated_caution", regulated_caution=True)
    assert_condition(
        failures,
        any(term in text for term in ["cannot", "can't", "not", "needs verified", "review"]),
        f"{vertical}/regulated_caution: missing direct unsafe-claim refusal: {snapshot(packet)}",
    )
    record(evidence, vertical, "regulated_caution", packet)


def validate_fallback_repair(failures: list[str], campaign: dict[str, Any], evidence: list[dict[str, Any]], vertical: str) -> None:
    packets = run_sequence(campaign, FALLBACK_REPAIR_TURNS, f"{CHECKPOINT_ID}-{vertical}-fallback-repair")
    for index, packet in enumerate(packets, start=1):
        assert_text_quality(failures, packet, campaign, f"{vertical}/fallback_repair/turn-{index}")
        if index >= 3:
            text = normalize(final_response(packet))
            assert_condition(failures, "password" not in text or "not the right" in text or "cannot" in text or "team" in text, f"{vertical}/fallback_repair: weak out-of-scope redirect")
    assert_no_repeated_sentence(failures, packets, f"{vertical}/fallback_repair")
    record(evidence, vertical, "fallback_repair", packets[-1])


def record(evidence: list[dict[str, Any]], vertical: str, scenario: str, packet: dict[str, Any]) -> None:
    frame = semantic_frame(packet)
    evidence.append(
        sanitize(
            {
                "vertical": vertical,
                "scenario": scenario,
                "transcript": packet.get("transcript"),
                "semantic": frame.get("semantic"),
                "target_gap": frame.get("target_gap"),
                "final_response": final_response(packet),
                "tts_input_text": tts_input_text(packet),
                "provider_rendered_text": provider_rendered_text(packet),
                "call_control": (packet.get("summary") or {}).get("call_control"),
            }
        )
    )


def validate_dynamic_quality(failures: list[str], evidence: dict[str, Any]) -> None:
    campaigns = synthetic_campaigns()
    rows: list[dict[str, Any]] = []
    for vertical in TARGET_VERTICALS:
        campaign = campaigns[vertical]
        for validator in [
            validate_opening,
            validate_permission,
            validate_current_gap_clear,
            validate_pain_confirmed,
            validate_send_info,
            validate_right_person,
            validate_regulated_caution,
            validate_fallback_repair,
        ]:
            before = len(rows)
            validator(failures, campaign, rows, vertical)
            for row in rows[before:]:
                packet_label = f"{vertical}/{row.get('scenario')}"
                # Re-run safety/playbook checks from the captured scenario packet by rebuilding is noisy;
                # the scenario validators already checked the live packet quality before recording.
                assert_condition(failures, bool(row.get("final_response")), f"{packet_label}: missing final response")
    evidence["dynamic_scenarios"] = rows


def validate_all_packets_common(failures: list[str]) -> None:
    campaigns = synthetic_campaigns()
    for vertical in TARGET_VERTICALS:
        campaign = campaigns[vertical]
        state: dict[str, Any] = {"turns": []}
        for index, transcript in enumerate(["__agent_open__", "yeah sure", first_gap_clear_phrase(campaign)], start=1):
            packet = run_turn(campaign, transcript, state, f"{CHECKPOINT_ID}-{vertical}-common")
            assert_generic_playbook(failures, packet, f"{vertical}/common/turn-{index}")
            assert_safety(failures, packet, f"{vertical}/common/turn-{index}")


def validate_route_signal(failures: list[str], evidence: dict[str, Any]) -> None:
    validate_routesignal_preservation(failures, evidence)


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# GENERIC-CAMPAIGN-RESPONSE-QUALITY-001",
        "",
        f"- Status: `{result['status']}`",
        f"- Failure count: `{result['failure_count']}`",
        f"- Verticals tested: `{', '.join(result['verticals_tested'])}`",
        f"- Scenarios covered: `{', '.join(result['scenarios_tested'])}`",
        f"- Response quality failures before patch: `{result.get('quality_failures_before_patch', {}).get('red_run_failure_count')}`",
        f"- RouteSignal preservation: `{str(result.get('routesignal_preservation_checked')).lower()}`",
        f"- Provider calls made: `{str(result['safety']['provider_calls_made']).lower()}`",
        f"- Local LLM calls made: `{str(result['safety']['local_llm_calls_made']).lower()}`",
        "",
        "## Wording Rules Added",
        "",
    ]
    lines.extend(f"- {rule}" for rule in result.get("wording_rules_added") or [])
    lines.extend(["", "## Failures", ""])
    if result.get("failures"):
        lines.extend(f"- {failure}" for failure in result["failures"])
    else:
        lines.append("- None")
    lines.extend(["", "## Dynamic Scenario Samples", ""])
    for row in result.get("dynamic_scenarios") or []:
        lines.append(f"- `{row.get('vertical')}` `{row.get('scenario')}` `{row.get('semantic')}`: {row.get('final_response')}")
    lines.extend(["", "## Patches Made", ""])
    lines.extend(f"- {patch}" for patch in result.get("patches_made") or [])
    return "\n".join(lines) + "\n"


def main() -> int:
    failures: list[str] = []
    evidence: dict[str, Any] = {}
    validate_dynamic_quality(failures, evidence)
    validate_all_packets_common(failures)
    validate_route_signal(failures, evidence)

    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "pass" if not failures else "fail",
        "failure_count": len(failures),
        "failures": failures,
        "dynamic_scenarios": evidence.get("dynamic_scenarios") or [],
        "routesignal_preservation": sanitize(evidence.get("routesignal_preservation") or {}),
        "routesignal_preservation_checked": bool(evidence.get("routesignal_preservation")),
        "verticals_tested": TARGET_VERTICALS,
        "scenarios_tested": [
            "opening",
            "permission_to_diagnostic",
            "current_gap_clear",
            "pain_confirmed",
            "send_info",
            "right_person_handoff",
            "regulated_caution",
            "fallback_repair",
        ],
        "wording_rules_added": [
            "final_response must not contain raw snake_case gap IDs.",
            "final_response must not contain double spaces, broken punctuation, internal runtime terms, or forbidden RouteSignal terms.",
            "generic responses avoid unnatural 'with <owner>', repeated 'safe check', clunky 'creating issues', and robotic if-X-matters phrasing.",
            "most generic turns stay at two sentences or fewer; regulated cautions may use three.",
            "final_response and tts_input_text must preserve the same meaning after filler and SSML cleanup.",
        ],
        "quality_failures_before_patch": QUALITY_FAILURES_BEFORE_PATCH,
        "patches_made": PATCHES_MADE,
        "phase_1_2_3_backpatch_required": False,
        "raw_synthetic_emails_in_public_evidence": False,
        "safety": {key: False for key in SAFETY_KEYS},
    }
    serialized = json.dumps(sanitize(result)).lower()
    result["raw_synthetic_emails_in_public_evidence"] = any(raw in serialized for raw in RAW_EMAILS)
    if result["raw_synthetic_emails_in_public_evidence"]:
        result["failures"].append("public generated evidence leaked raw synthetic email")
        result["failure_count"] = len(result["failures"])
        result["status"] = "fail"
    write_evidence(result, render_report(result))
    if result["status"] != "pass":
        print(json.dumps({"status": "fail", "failure_count": result["failure_count"], "result_path": str(RESULT_PATH)}, indent=2))
        return 1
    print(json.dumps({"status": "pass", "failure_count": 0, "result_path": str(RESULT_PATH)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
