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
from scripts.validate_generic_campaign_response_quality_001 import (  # noqa: E402
    PAIN_PHRASES,
    RISKY_QUESTIONS,
    first_gap_clear_phrase,
    provider_rendered_text,
    tts_input_text,
)
from scripts.validate_generic_campaign_runtime_regression_001 import synthetic_campaigns  # noqa: E402


CHECKPOINT_ID = "GENERIC-CAMPAIGN-SPOKEN-TEXT-QUALITY-001"
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
FILLER_WORDS = ["well", "so", "um", "uh"]
FILLER_BEFORE_TERMS = [
    "which",
    "what",
    "when",
    "who",
    "where",
    "why",
    "how",
    "do you",
    "should i",
    "can you",
]
PROTECTED_SCENARIOS = {
    "send_info",
    "callback_time_capture",
    "right_person_handoff",
    "stop_refusal",
    "regulated_caution",
}
SAFETY_KEYS = [
    "provider_calls_made",
    "local_llm_calls_made",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
]
SPOKEN_FAILURES_BEFORE_PATCH = {
    "red_run_failure_count": 528,
    "clusters": [
        "Visible speech-realism fillers appeared before direct diagnostic questions.",
        "Fillers were inserted after diagnostic-list commas, producing lines such as 'visibility gap, well, which...'.",
        "Protected send-info, callback, right-person, and regulated-caution scenario turns inherited filler from earlier generic turns.",
        "Connected speech folded sentence-boundary fillers into key questions, making otherwise acceptable final_response text sound hesitant.",
    ],
}
PATCHES_MADE = [
    "Disabled visible filler and speech-imperfection insertion for non-RouteSignal generic campaign configs in runtime voice delivery.",
    "Kept generic campaigns eligible for provider rendering, pauses, and non-word prosody metadata while preventing filler words from entering spoken text.",
    "Left RouteSignal live-demo voice shaping unchanged by excluding known RouteSignal campaign IDs from the generic voice guard.",
]


def write_evidence(result: dict[str, Any], report: str) -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(report, encoding="utf-8")


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def strip_ssml(text: str) -> str:
    return re.sub(r"<break[^>]*>", " ", str(text or ""), flags=re.IGNORECASE)


def clean_for_meaning(text: str) -> str:
    value = strip_ssml(text)
    value = value.replace("I'm", "I am").replace("don't", "do not").replace("can't", "cannot")
    value = re.sub(r"\b(?:well|so|um|uh)\b[, ]*", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"[^a-zA-Z0-9$ ]+", " ", value)
    return re.sub(r"\s+", " ", value).strip().lower()


def token_set(text: str) -> set[str]:
    stop = {"a", "an", "and", "or", "the", "to", "for", "of", "in", "on", "it", "is", "am", "are", "be"}
    return {word for word in clean_for_meaning(text).split() if len(word) > 2 and word not in stop}


def word_count_without_ssml(text: str) -> int:
    return len(re.findall(r"\b[\w$]+\b", strip_ssml(text)))


def break_count(text: str) -> int:
    return len(re.findall(r"<break\b[^>]*>", str(text or ""), flags=re.IGNORECASE))


def filler_matches(text: str) -> list[str]:
    return re.findall(r"\b(?:well|so|um|uh)\b", strip_ssml(text), flags=re.IGNORECASE)


def forbidden_matches(text: str) -> list[str]:
    lowered = normalize(strip_ssml(text))
    return [term for term in FORBIDDEN_TERMS if term.lower() in lowered]


def raw_snake_case_terms(text: str) -> list[str]:
    return sorted(set(re.findall(r"\b[a-z][a-z0-9]+(?:_[a-z0-9]+)+\b", strip_ssml(text))))


def filler_before_question(text: str) -> bool:
    cleaned = strip_ssml(text)
    for question_term in FILLER_BEFORE_TERMS:
        if re.search(rf"\b(?:well|so|um|uh)\b[\s,;:\-]*(?:<[^>]+>\s*)?{re.escape(question_term)}\b", cleaned, flags=re.IGNORECASE):
            return True
    return False


def filler_after_list_comma(text: str) -> bool:
    return bool(re.search(r",\s+\b(?:well|so|um|uh)\b[\s,;:\-]*(?:which|what|do you|should i)\b", strip_ssml(text), flags=re.IGNORECASE))


def break_inside_short_phrase(text: str, campaign: dict[str, Any]) -> list[str]:
    checks: list[tuple[str, str]] = [
        ("article_role", r"\b(?:a|an|the)\s*<break\b[^>]*>\s+\w+"),
        ("email_callback", r"\bemail\s*(?:or\s*)?<break\b[^>]*>\s*(?:or\s*)?callback\b"),
        ("callback_time", r"\bcallback\s*<break\b[^>]*>\s*time\b"),
    ]
    offer = str(campaign.get("product_or_offer_name") or campaign.get("offer_name") or "")
    offer_tokens = [re.escape(token) for token in offer.split() if token]
    if len(offer_tokens) >= 2:
        checks.append(("offer_name", r"\b" + r"\s*<break\b[^>]*>\s*".join(offer_tokens) + r"\b"))
    owner = str(campaign.get("human_followup_owner") or "")
    owner_tokens = [re.escape(token) for token in owner.split() if token]
    if len(owner_tokens) >= 2:
        checks.append(("owner_role", r"\b" + r"\s*<break\b[^>]*>\s*".join(owner_tokens) + r"\b"))
    return [name for name, pattern in checks if re.search(pattern, text, flags=re.IGNORECASE)]


def business_meaning_violations(final: str, spoken: str) -> list[str]:
    final_clean = clean_for_meaning(final)
    spoken_clean = clean_for_meaning(spoken)
    violations: list[str] = []
    schedule_terms = {"scheduled", "booked", "confirmed on the calendar", "calendar event"}
    if not any(term in final_clean for term in schedule_terms) and any(term in spoken_clean for term in schedule_terms):
        violations.append("spoken_text_added_schedule")
    guarantee_terms = {"guarantee", "guaranteed", "promise coverage", "promise a refund", "promise repair cost"}
    if not any(term in final_clean for term in guarantee_terms) and any(term in spoken_clean for term in guarantee_terms):
        violations.append("spoken_text_added_guarantee")
    if "stop" in final_clean and "continue" in spoken_clean:
        violations.append("spoken_text_softened_stop")
    final_tokens = token_set(final)
    spoken_tokens = token_set(spoken)
    if final_tokens:
        overlap = len(final_tokens & spoken_tokens) / max(1, len(final_tokens))
        if overlap < 0.72:
            violations.append(f"low_action_meaning_overlap:{overlap:.2f}")
    return violations


def text_sources(packet: dict[str, Any]) -> dict[str, str]:
    return {
        "final_response": final_response(packet),
        "tts_input_text": tts_input_text(packet),
        "provider_rendered_text": provider_rendered_text(packet),
    }


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
    assert_condition(failures, packet.get("durable_provider_agent_created") is False, f"{label}: durable_provider_agent_created must be false")
    assert_condition(failures, packet.get("voice_cloning_used") is False, f"{label}: voice_cloning_used must be false")


def assert_generic_playbook(failures: list[str], packet: dict[str, Any], label: str) -> None:
    playbook_id = str(packet.get("campaign_playbook_id") or "")
    assert_condition(
        failures,
        bool(playbook_id and playbook_id != ROUTESIGNAL_PLAYBOOK_ID),
        f"{label}: generic packet used RouteSignal/default playbook: {snapshot(packet)}",
    )


def assert_spoken_quality(
    failures: list[str],
    packet: dict[str, Any],
    campaign: dict[str, Any],
    label: str,
    *,
    scenario_id: str,
) -> None:
    assert_generic_playbook(failures, packet, label)
    assert_safety(failures, packet, label)
    final = final_response(packet)
    for source_name, text in text_sources(packet).items():
        if not text:
            continue
        found = forbidden_matches(text)
        assert_condition(failures, not found, f"{label}: {source_name} leaked generic RouteSignal terms {found}: {sanitize(text)}")
        snake = raw_snake_case_terms(text)
        assert_condition(failures, not snake, f"{label}: {source_name} exposed raw label ids {snake}: {sanitize(text)}")
        if source_name != "final_response":
            fillers = filler_matches(text)
            assert_condition(failures, len(fillers) <= 1, f"{label}: {source_name} has repeated filler {fillers}: {sanitize(text)}")
            if scenario_id in PROTECTED_SCENARIOS:
                assert_condition(failures, not fillers, f"{label}: {source_name} used filler in protected {scenario_id}: {sanitize(text)}")
            assert_condition(failures, not filler_before_question(text), f"{label}: {source_name} put filler before the key question: {sanitize(text)}")
            assert_condition(failures, not filler_after_list_comma(text), f"{label}: {source_name} put filler after a diagnostic list comma: {sanitize(text)}")
            if word_count_without_ssml(text) < 30:
                assert_condition(
                    failures,
                    break_count(text) <= 2,
                    f"{label}: {source_name} has too many break tags for a short response: {sanitize(text)}",
                )
            bad_breaks = break_inside_short_phrase(text, campaign)
            assert_condition(failures, not bad_breaks, f"{label}: {source_name} split short phrase units {bad_breaks}: {sanitize(text)}")
            meaning = business_meaning_violations(final, text)
            assert_condition(failures, not meaning, f"{label}: {source_name} changed action meaning {meaning}: final={sanitize(final)} spoken={sanitize(text)}")


def record(evidence: list[dict[str, Any]], vertical: str, scenario_id: str, packet: dict[str, Any]) -> None:
    frame = semantic_frame(packet)
    evidence.append(
        sanitize(
            {
                "vertical": vertical,
                "scenario_id": scenario_id,
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


def scenario_sequences(campaign: dict[str, Any], vertical: str) -> dict[str, list[str]]:
    return {
        "opening": ["__agent_open__"],
        "permission_to_diagnostic": ["__agent_open__", "yeah sure"],
        "current_gap_clear": ["__agent_open__", "yeah sure", first_gap_clear_phrase(campaign)],
        "pain_confirmed": ["__agent_open__", "yeah sure", PAIN_PHRASES[vertical]],
        "send_info": ["__agent_open__", "yeah sure", "send me details", "yes send it"],
        "callback_time_capture": ["__agent_open__", "yeah sure", "send me details", "tomorrow at 3 works"],
        "right_person_handoff": ["__agent_open__", "yeah sure", "I'm not the person", "operations handles that"],
        "stop_refusal": ["__agent_open__", "stop calling"],
        "regulated_caution": ["__agent_open__", "yeah sure", RISKY_QUESTIONS[vertical]],
        "fallback_repair": [
            "__agent_open__",
            "yeah sure",
            "what is this about?",
            "I don't understand",
            "what happens next?",
            "is it expensive?",
            "can you help with my password?",
        ],
    }


def validate_dynamic_scenarios(failures: list[str], evidence: dict[str, Any]) -> None:
    campaigns = synthetic_campaigns()
    rows: list[dict[str, Any]] = []
    for vertical in TARGET_VERTICALS:
        campaign = campaigns[vertical]
        for scenario_id, sequence in scenario_sequences(campaign, vertical).items():
            packets = run_sequence(campaign, sequence, f"{CHECKPOINT_ID}-{vertical}-{scenario_id}")
            for turn_index, packet in enumerate(packets, start=1):
                label = f"{vertical}/{scenario_id}/turn-{turn_index}/{packet.get('transcript')}"
                assert_spoken_quality(failures, packet, campaign, label, scenario_id=scenario_id)
            last_packet = packets[-1]
            if scenario_id == "send_info":
                text = normalize(strip_ssml(tts_input_text(last_packet)))
                assert_condition(failures, "email" in text and "callback" in text, f"{vertical}/send_info: spoken text missed email/callback path")
                assert_condition(failures, "sent" not in text and "scheduled" not in text, f"{vertical}/send_info: spoken text implied fake send/schedule")
            if scenario_id == "callback_time_capture":
                text = normalize(strip_ssml(tts_input_text(last_packet)))
                assert_condition(failures, "calendar" not in text and "event" not in text, f"{vertical}/callback_time_capture: calendar/event claim")
            if scenario_id == "stop_refusal":
                text = normalize(strip_ssml(tts_input_text(last_packet)))
                assert_condition(failures, "stop" in text or "goodbye" in text, f"{vertical}/stop_refusal: stop close not clear")
            record(rows, vertical, scenario_id, last_packet)
    evidence["dynamic_scenarios"] = rows


def validate_route_signal(failures: list[str], evidence: dict[str, Any]) -> None:
    validate_routesignal_preservation(failures, evidence)


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# GENERIC-CAMPAIGN-SPOKEN-TEXT-QUALITY-001",
        "",
        f"- Status: `{result['status']}`",
        f"- Failure count: `{result['failure_count']}`",
        f"- Verticals tested: `{', '.join(result['verticals_tested'])}`",
        f"- Scenarios covered: `{', '.join(result['scenarios_tested'])}`",
        f"- Spoken-text failures before patch: `{result.get('spoken_failures_before_patch', {}).get('red_run_failure_count')}`",
        f"- RouteSignal preservation: `{str(result.get('routesignal_preservation_checked')).lower()}`",
        f"- Provider calls made: `{str(result['safety']['provider_calls_made']).lower()}`",
        f"- Local LLM calls made: `{str(result['safety']['local_llm_calls_made']).lower()}`",
        "",
        "## Spoken Quality Rules",
        "",
    ]
    lines.extend(f"- {rule}" for rule in result.get("spoken_quality_rules") or [])
    lines.extend(["", "## Failures", ""])
    if result.get("failures"):
        lines.extend(f"- {failure}" for failure in result["failures"])
    else:
        lines.append("- None")
    lines.extend(["", "## Scenario Samples", ""])
    for row in result.get("dynamic_scenarios") or []:
        lines.append(f"- `{row.get('vertical')}` `{row.get('scenario_id')}` `{row.get('semantic')}`: {row.get('tts_input_text')}")
    lines.extend(["", "## Patches Made", ""])
    if result.get("patches_made"):
        lines.extend(f"- {patch}" for patch in result["patches_made"])
    else:
        lines.append("- None yet; validator captured current behavior.")
    return "\n".join(lines) + "\n"


def main() -> int:
    failures: list[str] = []
    evidence: dict[str, Any] = {}
    validate_dynamic_scenarios(failures, evidence)
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
        "scenarios_tested": sorted(scenario_sequences(next(iter(synthetic_campaigns().values())), "b2b_saas")),
        "spoken_quality_rules": [
            "No RouteSignal leakage in final_response, tts_input_text, or provider-rendered dry-run text.",
            "No filler in stop/refusal, regulated caution, callback confirmation, send-info capture, or right-person capture.",
            "No more than one filler marker in any generic spoken response.",
            "No filler immediately before direct question words or after a diagnostic-list comma.",
            "Short generic responses under 30 words may not contain more than two SSML break tags.",
            "Break tags may not split role articles, owner roles, offer names, or email/callback-time phrases.",
            "Spoken text must not add scheduling, guarantees, product facts, or soften stop/refusal meaning.",
        ],
        "spoken_failures_before_patch": SPOKEN_FAILURES_BEFORE_PATCH,
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
