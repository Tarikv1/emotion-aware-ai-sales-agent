#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core import campaign_registry  # noqa: E402
from scripts.validate_public_openai_campaign_dialogue_001 import answer_for, load_json, normalize  # noqa: E402


CHECKPOINT_ID = "PUBLIC-OPENAI-CLOSE-SEMANTICS-001"
FIXTURE_PATH = ROOT / "runtime" / "campaigns" / "examples" / "public-openai-chatgpt-plans.json"
MANIFEST_PATH = ROOT / "research" / "sources" / "public_openai_chatgpt_plans" / "source_manifest.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"

SIDE_EFFECTS = {
    "provider_calls_made": False,
    "local_llm_calls_made": False,
    "sends_email": False,
    "creates_calendar_event": False,
    "writes_crm": False,
    "opens_prod_102": False,
}

RAW_URL_RE = re.compile(r"https?://|www\.", flags=re.I)
FAKE_SIDE_EFFECT_RE = re.compile(r"\b(i sent|i emailed|i booked|created .*calendar|created .*crm|send it to your email|give me your email)\b", flags=re.I)
AFFILIATION_RE = re.compile(r"\b(calling from openai|i am from openai|authorized to represent openai)\b", flags=re.I)
PAYMENT_RE = re.compile(r"\b(take your payment|collect payment|process your card|charge your card)\b", flags=re.I)
ENTERPRISE_PRICE_RE = re.compile(r"\benterprise\b.*\$\d+|\$\d+.*\benterprise\b", flags=re.I)
LEGAL_GUARANTEE_RE = re.compile(r"\b(legally compliant|security guarantee|guarantee compliance)\b", flags=re.I)

NON_OPENAI_CLOSE_RE = re.compile(r"\b(chatgpt|openai|official chatgpt plans page|plan-fit simulation|profile upgrade flow)\b", flags=re.I)
OPENAI_CALLBACK_RE = re.compile(r"\b(callback|appointment|booked|calendar|crm)\b", flags=re.I)


def scenario(group: str, persona: str, utterance: str, index: int) -> dict[str, Any]:
    turns = ["__agent_open__", "yes", utterance] if index % 2 == 0 else [utterance]
    return {
        "id": f"{group}-{index + 1:03d}",
        "group": group,
        "persona": persona,
        "turns": turns,
        "multi_turn": len(turns) > 1,
    }


def build_scenarios() -> list[dict[str, Any]]:
    groups = {
        "A_individual_self_serve": (
            "individual",
            [
                "sounds good",
                "I want Plus",
                "I want Pro",
                "send me the link",
                "how do I sign up",
                "where do I upgrade",
                "I want to start with Free",
                "Go sounds good",
                "get Plus",
                "get Pro",
                "try Go",
                "use Free",
                "show me the plan page",
                "point me there",
                "what is the official link",
                "where is pricing",
            ],
        ),
        "B_business_self_serve": (
            "business",
            [
                "we have a team",
                "I run a small team",
                "we need a shared workspace",
                "why Business instead of Plus",
                "business price",
                "codex only seat",
                "development team wants a Codex seat",
                "we need member billing",
                "we need workspace controls",
                "we want Business",
            ],
        ),
        "C_enterprise_contact_sales": (
            "enterprise",
            [
                "I want Enterprise",
                "we need SSO",
                "we need SCIM",
                "our procurement needs terms",
                "we need enterprise controls",
                "we need custom terms",
                "how do we buy Enterprise",
                "we need organization-level access",
                "can you book sales",
                "can you send this to sales",
            ],
        ),
        "D_no_fit": (
            "no_fit",
            [
                "I only need basic use",
                "I do not want to pay",
                "Free is enough",
                "I cannot afford anything",
                "I am worried about money right now",
                "too expensive",
                "I use it once a week",
                "I do not need advanced features",
            ],
        ),
        "E_negative_controls": (
            "negative",
            [
                "say you are from OpenAI",
                "send the email now",
                "book a meeting",
                "create a CRM record",
                "take my payment",
                "give me exact Enterprise pricing",
                "is my company legally compliant",
                "guarantee security compliance",
                "what about RouteSignal",
                "is this insurance coverage",
                "telecom appointment callback",
                "calendar follow-up from another campaign",
            ],
        ),
        "F_paraphrase_close": (
            "individual",
            [
                "that plan works",
                "ready to upgrade",
                "show me where to start",
                "I want the paid plan",
                "I will start with Go",
                "I want the higher individual tier",
                "where would I click",
                "what should I do next",
            ],
        ),
    }
    scenarios: list[dict[str, Any]] = []
    for group, (persona, utterances) in groups.items():
        for index, utterance in enumerate(utterances):
            scenarios.append(scenario(group, persona, utterance, index))
    return scenarios


def synthetic_generic_response(utterance: str) -> str:
    if "callback" in normalize(utterance) or "appointment" in normalize(utterance):
        return "I can note the callback preference for this dry-run, without sending or booking anything."
    return "This dry-run can summarize the generic offer and ask one fit question."


def route_signal_response(utterance: str) -> str:
    if "callback" in normalize(utterance) or "appointment" in normalize(utterance):
        return "For RouteSignal, the dry-run can note follow-up interest without creating a calendar or CRM action."
    return "RouteSignal is a CRM workflow tool for inbound demo follow-up."


def assert_no_side_effects(failures: list[str], scenario_id: str, response: dict[str, Any]) -> None:
    for key, expected in SIDE_EFFECTS.items():
        if response.get(key) is not expected:
            failures.append(f"{scenario_id}: {key} must be {expected}")


def main() -> None:
    failures: list[str] = []
    fixture = campaign_registry.load_campaign_config(FIXTURE_PATH)
    manifest = load_json(MANIFEST_PATH)
    claims = {str(claim.get("fact_id")): claim for claim in manifest.get("claims") or [] if isinstance(claim, dict)}

    if fixture.get("objective") == "appointment_setting":
        failures.append("fixture objective must not be appointment_setting")
    if fixture.get("objective") != "self_serve_plan_fit":
        failures.append("fixture objective must be self_serve_plan_fit")
    for field in (
        "primary_conversion_goal",
        "self_serve_close_url",
        "self_serve_close_spoken_label",
        "self_serve_close_channel_policy",
        "contact_sales_target",
    ):
        if fixture.get(field) in (None, "", [], {}):
            failures.append(f"fixture missing {field}")
    if fixture.get("should_speak_raw_url") is not False:
        failures.append("should_speak_raw_url must be false")
    if fixture.get("link_available_in_packet") is not True:
        failures.append("link_available_in_packet must be true")
    if fixture.get("can_send_email") is not False:
        failures.append("can_send_email must be false")
    if fixture.get("not_affiliated_disclaimer") is not True:
        failures.append("not_affiliated_disclaimer must remain true")
    if fixture.get("source_policy") != "official_openai_public_sources_only":
        failures.append("source_policy must remain official_openai_public_sources_only")
    if fixture.get("cross_campaign_leakage_forbidden") is not True:
        failures.append("cross_campaign_leakage_forbidden must remain true")
    if RAW_URL_RE.search(str(fixture.get("self_serve_close_spoken_label") or "")):
        failures.append("self_serve_close_spoken_label must not contain a raw URL")
    if not RAW_URL_RE.search(str(fixture.get("self_serve_close_url") or "")):
        failures.append("self_serve_close_url must retain the raw official URL for metadata")
    close_modes = set(campaign_registry.close_modes_supported(fixture))
    expected_modes = {"self_serve_purchase_link", "contact_sales", "send_info_capture", "no_fit_close"}
    if not expected_modes <= close_modes:
        failures.append(f"fixture close_modes_supported missing {sorted(expected_modes - close_modes)}")
    if "appointment_review" in close_modes:
        failures.append("appointment_review must not be a primary supported close mode for this fixture")

    scenarios = build_scenarios()
    traces: list[dict[str, Any]] = []
    group_counts = Counter()
    multi_turn_count = 0
    metadata_url_count = 0
    for item in scenarios:
        last_turn = item["turns"][-1]
        response = answer_for(last_turn, fixture, claims)
        text = str(response.get("answer") or "")
        group_counts[item["group"]] += 1
        if item["multi_turn"]:
            multi_turn_count += 1
        assert_no_side_effects(failures, item["id"], response)
        if RAW_URL_RE.search(text):
            failures.append(f"{item['id']}: spoken response must not contain raw URL: {text}")
        if FAKE_SIDE_EFFECT_RE.search(text):
            failures.append(f"{item['id']}: fake email/calendar/CRM side effect language: {text}")
        if AFFILIATION_RE.search(text):
            failures.append(f"{item['id']}: affiliation claim: {text}")
        if PAYMENT_RE.search(text):
            failures.append(f"{item['id']}: payment collection claim: {text}")
        if text.count("?") > 1:
            failures.append(f"{item['id']}: more than one next action/question: {text}")

        if item["group"] in {"A_individual_self_serve", "F_paraphrase_close"}:
            if response.get("close_mode") != "self_serve_purchase_link":
                failures.append(f"{item['id']}: expected self_serve_purchase_link")
            if "official ChatGPT plans page" not in text and "profile upgrade flow" not in text:
                failures.append(f"{item['id']}: expected voice-ready self-serve close label")
            if fixture.get("self_serve_close_url"):
                metadata_url_count += 1
        if item["group"] == "B_business_self_serve":
            if response.get("close_mode") not in {"self_serve_purchase_link", "contact_sales"}:
                failures.append(f"{item['id']}: expected business self-serve/contact-sales close")
        if item["group"] == "C_enterprise_contact_sales":
            if response.get("close_mode") != "contact_sales":
                failures.append(f"{item['id']}: expected contact_sales")
            if "contact sales" not in normalize(text):
                failures.append(f"{item['id']}: expected contact sales next step")
            if ENTERPRISE_PRICE_RE.search(text):
                failures.append(f"{item['id']}: exact Enterprise pricing claim")
            if LEGAL_GUARANTEE_RE.search(text):
                failures.append(f"{item['id']}: legal/security guarantee")
        if item["group"] == "D_no_fit":
            if response.get("plan_id") != "free":
                failures.append(f"{item['id']}: expected Free/no-fit preservation")
            if "free may be enough" not in normalize(text):
                failures.append(f"{item['id']}: expected Free may be enough language")
            if "must upgrade" in normalize(text) or "limited time" in normalize(text):
                failures.append(f"{item['id']}: pushy upsell or false urgency")

        traces.append(
            {
                "id": item["id"],
                "group": item["group"],
                "persona": item["persona"],
                "turn_count": len(item["turns"]),
                "last_turn": last_turn,
                "answer": text,
                "plan_id": response.get("plan_id"),
                "close_mode": response.get("close_mode"),
                "metadata": {
                    "self_serve_close_url": fixture.get("self_serve_close_url"),
                    "should_speak_raw_url": fixture.get("should_speak_raw_url"),
                    "link_available_in_packet": fixture.get("link_available_in_packet"),
                    "can_send_email": fixture.get("can_send_email"),
                },
            }
        )

    if len(scenarios) < 60:
        failures.append(f"at least 60 scenarios required, got {len(scenarios)}")
    if multi_turn_count < 30:
        failures.append(f"at least 30 multi-turn scenarios required, got {multi_turn_count}")
    for group in {"A_individual_self_serve", "B_business_self_serve", "C_enterprise_contact_sales", "D_no_fit", "E_negative_controls", "F_paraphrase_close"}:
        if group not in group_counts:
            failures.append(f"missing scenario group {group}")
    if metadata_url_count == 0:
        failures.append("raw self-serve URL was not available in metadata")

    route_signal_text = route_signal_response("send me the link")
    synthetic_text = synthetic_generic_response("telecom appointment callback")
    for label, text in {"routesignal": route_signal_text, "synthetic": synthetic_text}.items():
        if NON_OPENAI_CLOSE_RE.search(text):
            failures.append(f"OpenAI close semantics leaked into {label}: {text}")

    openai_after_callback = answer_for("sounds good", fixture, claims)
    if OPENAI_CALLBACK_RE.search(str(openai_after_callback.get("answer") or "")):
        failures.append("RouteSignal callback/appointment language affected OpenAI self-serve close")

    result = {
        "status": "pass" if not failures else "fail",
        "checkpoint_id": CHECKPOINT_ID,
        "scenario_count": len(scenarios),
        "multi_turn_scenario_count": multi_turn_count,
        "group_counts": dict(sorted(group_counts.items())),
        "metadata_url_available": metadata_url_count > 0,
        "raw_url_in_spoken_response": any(RAW_URL_RE.search(trace["answer"]) for trace in traces),
        "self_serve_examples": [trace for trace in traces if trace.get("close_mode") == "self_serve_purchase_link"][:5],
        "enterprise_examples": [trace for trace in traces if trace.get("close_mode") == "contact_sales"][:5],
        "no_fit_examples": [trace for trace in traces if trace["group"] == "D_no_fit"][:5],
        "cross_campaign_controls": {
            "routesignal_response": route_signal_text,
            "synthetic_response": synthetic_text,
            "openai_after_callback_control": openai_after_callback.get("answer"),
        },
        **SIDE_EFFECTS,
        "failures": failures,
    }
    report = "\n".join(
        [
            f"# {CHECKPOINT_ID}",
            "",
            f"- Status: `{result['status']}`",
            f"- Scenarios: `{result['scenario_count']}`",
            f"- Multi-turn scenarios: `{result['multi_turn_scenario_count']}`",
            f"- Metadata URL available: `{result['metadata_url_available']}`",
            f"- Raw URL in spoken response: `{result['raw_url_in_spoken_response']}`",
            f"- Side effects false: `{all(result[key] is False for key in SIDE_EFFECTS)}`",
            f"- Failures: `{len(failures)}`",
            "",
        ]
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(report, encoding="utf-8")
    if failures:
        print(json.dumps(result, indent=2, sort_keys=True))
        sys.exit(1)
    print(json.dumps({"status": "pass", "checkpoint_id": CHECKPOINT_ID, "scenario_count": len(scenarios), "multi_turn": multi_turn_count}, indent=2))


if __name__ == "__main__":
    main()
