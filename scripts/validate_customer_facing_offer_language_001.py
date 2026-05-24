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
from runtime.entrypoints import generic_campaign_turn as generic_turn  # noqa: E402
from scripts import run_live_demo_001_agent_voice_call as demo  # noqa: E402


CHECKPOINT_ID = "CUSTOMER-FACING-OFFER-LANGUAGE-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID
EXAMPLES = ROOT / "runtime" / "campaigns" / "examples"

GENERIC_CONFIGS = [
    EXAMPLES / "synthetic-telecom-plan-review.json",
    EXAMPLES / "synthetic-insurance-review.json",
    EXAMPLES / "synthetic-automotive-service-review.json",
    EXAMPLES / "synthetic-membership-plan-review.json",
    EXAMPLES / "synthetic-b2b-saas-operations.json",
    EXAMPLES / "synthetic-home-services-estimate.json",
    EXAMPLES / "synthetic-healthcare-admin-review.json",
    EXAMPLES / "synthetic-retail-support-review.json",
]

CUSTOMER_FIELDS = (
    "customer_facing_company_name",
    "customer_facing_offer_name",
    "customer_facing_offer_summary",
    "customer_facing_value_proposition",
    "customer_facing_call_objective",
    "customer_facing_human_review_scope",
)

EXACT_BANNED_PHRASES = (
    "This synthetic campaign represents",
    "not a full product pitch",
    "Plan Review Call",
    "Policy Review Call",
    "Synthetic Telecom Provider",
    "Synthetic Insurance Agency",
    "Synthetic Membership Program",
    "Synthetic Automotive Service",
    "Synthetic Home Services",
    "review is the next step, not the product",
)

PARAPHRASE_BANNED_PATTERNS = (
    r"\bsynthetic (campaign|fixture|provider|agency|program|service|company)\b",
    r"\btest fixture\b",
    r"\binternal (fixture|policy|metadata|review target|campaign)\b",
    r"\bapproved (qualified )?(reviewer )?path\b",
    r"\bnot (?:a )?(?:complete|full) product pitch\b",
    r"\breview (?:is|as) the product\b",
    r"\bthe product is (?:a )?review\b",
    r"\bmechanical campaign metadata\b",
)

UNSUPPORTED_CLAIM_PATTERNS = (
    r"\bguarantee(?:d|s)?\b",
    r"\bpromise(?:d|s)?\b",
    r"\bexact (?:price|quote|premium|coverage|savings)\b",
    r"\bfor sure\b",
    r"\bwill save\b",
    r"\bbetter than your current provider\b",
    r"\bcovered\b.*\bfor sure\b",
    r"\bsecurity certified\b",
)

SIDE_EFFECT_KEYS = (
    "provider_calls_made",
    "local_llm_calls_made",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
)

PRODUCT_QUESTIONS = (
    "what are you selling",
    "what is your product",
    "what do you do",
    "what problem do you solve",
)

VALUE_QUESTIONS = (
    "why should I care",
    "what makes you different",
    "how do I know the difference from my current provider",
)

HUMAN_REVIEW_QUESTIONS = (
    "why do I need a human review",
    "why can't you just tell me",
    "what will the specialist check",
)

NEGATIVE_CONTROLS = (
    ("stop/refusal", "I don't want to continue"),
    ("serious hardship", "I am worried about money right now"),
    ("sensitive data", "what do you do with my data"),
    ("explicit price question", "what exact price"),
    ("regulated detail question", "can you guarantee that"),
)

EXPECTED_BY_CAMPAIGN = {
    "synthetic-telecom-plan-review": {
        "offer_fragment": "telecom plan fit check",
        "summary_fragments": ["plan fit", "coverage availability", "switching"],
        "value_fragments": ["bad-fit plan", "switching path", "account-specific"],
        "scope_fragments": ["plan fit", "coverage", "switching"],
    },
    "synthetic-insurance-review": {
        "offer_fragment": "policy fit check",
        "summary_fragments": ["premium pressure", "coverage fit", "renewal timing"],
        "value_fragments": ["licensed reviewer", "coverage", "premium"],
        "scope_fragments": ["premium pressure", "coverage fit", "renewal timing"],
    },
    "synthetic-automotive-service-review": {
        "offer_fragment": "service fit check",
        "summary_fragments": ["vehicle issue", "repair timing", "estimate"],
        "value_fragments": ["service advisor", "diagnosing", "estimate"],
        "scope_fragments": ["vehicle issue", "repair timing", "estimate"],
    },
    "synthetic-membership-plan-review": {
        "offer_fragment": "membership plan fit check",
        "summary_fragments": ["plan fit", "renewal", "usage"],
        "value_fragments": ["account support", "cancellation", "renewal"],
        "scope_fragments": ["plan fit", "renewal", "usage"],
    },
    "synthetic-b2b-saas-operations": {
        "offer_fragment": "operations fit check",
        "summary_fragments": ["manual work", "integration", "visibility"],
        "value_fragments": ["implementation specialist", "manual work", "integration"],
        "scope_fragments": ["manual work", "integration", "visibility"],
    },
    "synthetic-home-services-estimate": {
        "offer_fragment": "home service fit check",
        "summary_fragments": ["service need", "scheduling", "estimate"],
        "value_fragments": ["coordinator", "property", "estimate"],
        "scope_fragments": ["service need", "scheduling", "estimate"],
    },
    "synthetic-healthcare-admin-review": {
        "offer_fragment": "admin fit check",
        "summary_fragments": ["administrative issue", "scheduling", "billing"],
        "value_fragments": ["qualified specialist", "admin", "specific details"],
        "scope_fragments": ["administrative issue", "scheduling", "billing"],
    },
    "synthetic-retail-support-review": {
        "offer_fragment": "retail support fit check",
        "summary_fragments": ["order issue", "product support", "return"],
        "value_fragments": ["support specialist", "order", "support"],
        "scope_fragments": ["order issue", "product support", "return"],
    },
}


def normalize(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def contains_any(text: str, fragments: list[str] | tuple[str, ...]) -> bool:
    lowered = normalize(text)
    return any(normalize(fragment) in lowered for fragment in fragments if str(fragment or "").strip())


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError(f"{path.relative_to(ROOT)} must be a JSON object")
    return payload


def final_response(packet: dict[str, Any]) -> str:
    summary = packet.get("summary") or {}
    if summary.get("final_response"):
        return str(summary.get("final_response"))
    return str(packet.get("final_response") or ((packet.get("packet") or {}).get("final_response")) or "")


def tts_text(packet: dict[str, Any]) -> str:
    summary = packet.get("summary") or {}
    packet_body = packet.get("packet") or {}
    tts = packet_body.get("tts_delivery") or {}
    return str(summary.get("tts_input_text") or tts.get("tts_input_text") or "")


def append_turn(state: dict[str, Any], packet: dict[str, Any]) -> None:
    state.setdefault("turns", []).append(
        {
            "transcript": packet.get("transcript") or "",
            "summary": packet.get("summary") or {},
            "conversation_memory": packet.get("conversation_memory") or packet.get("demo_conversation_memory") or {},
            "conversation_continuity": packet.get("conversation_continuity") or packet.get("demo_session_continuity") or {},
            "dialogue_manager": packet.get("dialogue_manager") or {},
            "universal_policy_frame": packet.get("universal_policy_frame") or {},
        }
    )
    for key in ("conversation_memory", "conversation_continuity", "dialogue_manager", "universal_policy_frame"):
        if packet.get(key) is not None:
            state[key] = packet[key]


def build_generic_turn(config_path: Path, transcript: str, state: dict[str, Any], session_id: str) -> dict[str, Any]:
    packet = generic_turn.build_generic_campaign_turn_packet_from_config_path(
        transcript=transcript,
        campaign_config_path=config_path,
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


def build_routesignal_turn(transcript: str, state: dict[str, Any], session_id: str) -> dict[str, Any]:
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
        session_id=session_id,
        session_state=state,
        asr_confidence=0.94,
        generic_live_tts_allowed=False,
    )
    append_turn(state, packet)
    return packet


def clean_text_failures(text: str, *, label: str) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for phrase in EXACT_BANNED_PHRASES:
        if phrase.lower() in text.lower():
            failures.append({"check": "exact_banned_phrase", "label": label, "phrase": phrase, "text": text})
    for pattern in PARAPHRASE_BANNED_PATTERNS:
        if re.search(pattern, text, flags=re.I):
            failures.append({"check": "banned_paraphrase", "label": label, "pattern": pattern, "text": text})
    if re.search(r"\b(mainly,\s+this|mainly,\s+[A-Z])", text):
        failures.append({"check": "awkward_capitalization", "label": label, "text": text})
    if normalize(text).count("human review") > 2:
        failures.append({"check": "over_repeated_human_review", "label": label, "text": text})
    return failures


def side_effect_flags(packet: dict[str, Any]) -> dict[str, bool]:
    summary = packet.get("summary") or {}
    tts = ((packet.get("packet") or {}).get("tts_delivery") or {})
    return {
        "provider_calls_made": bool(packet.get("provider_calls_made") or tts.get("provider_calls_made")),
        "local_llm_calls_made": bool(packet.get("local_llm_calls_made")),
        "sends_email": bool(packet.get("sends_email")),
        "creates_calendar_event": bool(packet.get("creates_calendar_event")),
        "writes_crm": bool(packet.get("writes_crm")),
        "opens_prod_102": bool(packet.get("opens_prod_102")),
        "live_tts_used": bool(packet.get("live_tts_used") or summary.get("live_tts_used")),
        "audio_file_created": bool(packet.get("audio_file_created") or summary.get("tts_audio_file_created")),
    }


def assert_side_effects(failures: list[dict[str, Any]], packet: dict[str, Any], label: str) -> None:
    flags = side_effect_flags(packet)
    for key, value in flags.items():
        if value is not False:
            failures.append({"check": "side_effect_flag", "label": label, "key": key, "flags": flags})
    if packet.get("audio_url") not in (None, ""):
        failures.append({"check": "audio_url_created", "label": label, "audio_url": packet.get("audio_url")})


def static_config_checks(configs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for campaign_id, config in configs.items():
        expected = EXPECTED_BY_CAMPAIGN.get(campaign_id) or {}
        for field in CUSTOMER_FIELDS:
            value = str(config.get(field) or "").strip()
            if not value:
                failures.append({"check": "missing_customer_facing_field", "campaign_id": campaign_id, "field": field})
                continue
            failures.extend(clean_text_failures(value, label=f"{campaign_id}.{field}"))
        if not str(config.get("internal_fixture_description") or "").strip():
            failures.append({"check": "missing_internal_fixture_description", "campaign_id": campaign_id})
        offer_name = str(config.get("customer_facing_offer_name") or "")
        if expected.get("offer_fragment") and normalize(expected["offer_fragment"]) not in normalize(offer_name):
            failures.append(
                {
                    "check": "unexpected_customer_offer_name",
                    "campaign_id": campaign_id,
                    "expected_fragment": expected["offer_fragment"],
                    "actual": offer_name,
                }
            )
        for legacy_field in ("client_name", "product_or_offer_name"):
            legacy_value = str(config.get(legacy_field) or "")
            if legacy_field == "client_name" and "synthetic" not in normalize(legacy_value):
                failures.append({"check": "internal_fixture_name_not_preserved", "campaign_id": campaign_id, "field": legacy_field})
        for field in ("customer_facing_offer_name", "customer_facing_offer_summary"):
            value = str(config.get(field) or "")
            if value in {"Plan Review Call", "Policy Review Call", "Service Advisor Review"}:
                failures.append({"check": "review_call_used_as_product", "campaign_id": campaign_id, "field": field, "value": value})
    return failures


def opening_checks(configs: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    failures: list[dict[str, Any]] = []
    samples: list[dict[str, Any]] = []
    for index, (campaign_id, config) in enumerate(configs.items(), start=1):
        state: dict[str, Any] = {}
        packet = build_generic_turn(GENERIC_CONFIGS[index - 1], "__agent_open__", state, f"opening-{campaign_id}")
        text = final_response(packet)
        samples.append({"campaign_id": campaign_id, "response": text})
        failures.extend(clean_text_failures(text, label=f"{campaign_id}.opening"))
        assert_side_effects(failures, packet, f"{campaign_id}.opening")
        company = str(config.get("customer_facing_company_name") or "")
        offer = str(config.get("customer_facing_offer_name") or "")
        if company and company not in text:
            failures.append({"check": "opening_missing_company", "campaign_id": campaign_id, "expected": company, "text": text})
        if offer and normalize(offer) not in normalize(text):
            failures.append({"check": "opening_missing_offer", "campaign_id": campaign_id, "expected": offer, "text": text})
        expected = EXPECTED_BY_CAMPAIGN.get(campaign_id) or {}
        has_review_purpose = "worth" in normalize(text) and "review" in normalize(text)
        has_spoken_fit_scope = "fit check" in normalize(text) and contains_any(text, expected.get("summary_fragments") or [])
        if not has_review_purpose and not has_spoken_fit_scope:
            failures.append({"check": "opening_missing_review_purpose", "campaign_id": campaign_id, "text": text})
    return failures, samples


def route_or_generic_turn(
    campaign_id: str,
    config_path: Path | None,
    transcript: str,
    state: dict[str, Any],
    session_id: str,
) -> dict[str, Any]:
    if config_path is None:
        return build_routesignal_turn(transcript, state, session_id)
    return build_generic_turn(config_path, transcript, state, session_id)


def response_checks() -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    failures: list[dict[str, Any]] = []
    samples: list[dict[str, Any]] = []
    scenario_count = 0
    campaigns: list[tuple[str, Path | None]] = [("routesignal", None)] + [(read_json(path)["campaign_id"], path) for path in GENERIC_CONFIGS]

    groups = [
        ("product_offer_questions", PRODUCT_QUESTIONS),
        ("value_difference_questions", VALUE_QUESTIONS),
        ("human_review_questions", HUMAN_REVIEW_QUESTIONS),
    ]
    for group_name, questions in groups:
        for campaign_id, config_path in campaigns:
            expected = EXPECTED_BY_CAMPAIGN.get(campaign_id) or {
                "offer_fragment": "RouteSignal",
                "summary_fragments": ["CRM workflow tool", "inbound demo follow-up"],
                "value_fragments": ["missed replies", "ownership", "manual follow-up"],
                "scope_fragments": ["who owns the lead", "follow-up", "handoffs"],
            }
            for question in questions:
                scenario_count += 1
                state: dict[str, Any] = {}
                route_or_generic_turn(campaign_id, config_path, "__agent_open__", state, f"{group_name}-{scenario_count}-open")
                packet = route_or_generic_turn(campaign_id, config_path, question, state, f"{group_name}-{scenario_count}")
                text = final_response(packet)
                if len(samples) < 36:
                    samples.append({"group": group_name, "campaign_id": campaign_id, "question": question, "response": text})
                failures.extend(clean_text_failures(text, label=f"{campaign_id}.{group_name}.{question}"))
                assert_side_effects(failures, packet, f"{campaign_id}.{group_name}.{question}")
                if group_name == "product_offer_questions":
                    if not contains_any(text, [expected["offer_fragment"], *expected["summary_fragments"]]):
                        failures.append({"check": "product_answer_missing_offer_summary", "campaign_id": campaign_id, "question": question, "text": text})
                    if "review" in normalize(text) and not contains_any(text, [expected["offer_fragment"], *expected["summary_fragments"]]):
                        failures.append({"check": "review_framed_without_offer_summary", "campaign_id": campaign_id, "question": question, "text": text})
                    if "full menu" in normalize(text):
                        failures.append({"check": "product_answer_looks_like_menu", "campaign_id": campaign_id, "question": question, "text": text})
                elif group_name == "value_difference_questions":
                    if not contains_any(text, expected["value_fragments"]):
                        failures.append({"check": "value_answer_missing_value_proposition", "campaign_id": campaign_id, "question": question, "text": text})
                    for pattern in UNSUPPORTED_CLAIM_PATTERNS:
                        if re.search(pattern, text, flags=re.I):
                            failures.append({"check": "unsupported_claim", "campaign_id": campaign_id, "question": question, "pattern": pattern, "text": text})
                else:
                    if not contains_any(text, expected["scope_fragments"]):
                        failures.append({"check": "human_review_answer_missing_scope", "campaign_id": campaign_id, "question": question, "text": text})
                    if not contains_any(text, ["specialist", "reviewer", "licensed", "advisor", "support", "coordinator"]):
                        failures.append({"check": "human_review_answer_missing_human_owner", "campaign_id": campaign_id, "question": question, "text": text})
                    if contains_any(text, ["transferring you now", "I will transfer", "live transfer"]):
                        failures.append({"check": "fake_transfer_escalation", "campaign_id": campaign_id, "question": question, "text": text})

    for campaign_id, config_path in campaigns:
        for label, transcript in NEGATIVE_CONTROLS:
            scenario_count += 1
            state = {}
            route_or_generic_turn(campaign_id, config_path, "__agent_open__", state, f"negative-{scenario_count}-open")
            packet = route_or_generic_turn(campaign_id, config_path, transcript, state, f"negative-{scenario_count}")
            text = final_response(packet)
            failures.extend(clean_text_failures(text, label=f"{campaign_id}.negative.{label}"))
            assert_side_effects(failures, packet, f"{campaign_id}.negative.{label}")
            lowered = normalize(text)
            if label == "stop/refusal" and not contains_any(text, ["stop", "goodbye", "leave it here"]):
                failures.append({"check": "stop_refusal_not_preserved", "campaign_id": campaign_id, "text": text})
            if label == "serious hardship" and contains_any(text, ["what time works", "schedule", "book"]):
                failures.append({"check": "hardship_pushed_appointment", "campaign_id": campaign_id, "text": text})
            if label == "sensitive data" and not contains_any(text, ["sensitive", "data", "stop"]):
                failures.append({"check": "sensitive_data_boundary_missing", "campaign_id": campaign_id, "text": text})
            if label == "explicit price question" and re.search(r"\$\d+|\b\d+\s*(?:dollars|euros|per month)\b", lowered):
                failures.append({"check": "generic_or_regulated_price_quoted", "campaign_id": campaign_id, "text": text})
            if label == "regulated detail question" and contains_any(text, ["yes, I guarantee", "yes I guarantee", "I promise that", "for sure"]):
                failures.append({"check": "regulated_boundary_not_preserved", "campaign_id": campaign_id, "text": text})
    return failures, samples, scenario_count


def write_evidence(result: dict[str, Any], report: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> int:
    failures: list[dict[str, Any]] = []
    configs = {read_json(path)["campaign_id"]: campaign_registry.load_campaign_config(path) for path in GENERIC_CONFIGS}
    failures.extend(static_config_checks(configs))
    opening_failures, opening_samples = opening_checks(configs)
    failures.extend(opening_failures)
    response_failures, response_samples, scenario_count = response_checks()
    failures.extend(response_failures)

    failure_types = Counter(str(item.get("check") or "unknown") for item in failures)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "valid": not failures,
        "scenario_count": scenario_count + len(configs),
        "campaign_count": len(configs) + 1,
        "generic_campaign_count": len(configs),
        "failure_count": len(failures),
        "failure_types": dict(sorted(failure_types.items())),
        "failures": failures[:240],
        "banned_exact_phrases": list(EXACT_BANNED_PHRASES),
        "banned_paraphrase_patterns": list(PARAPHRASE_BANNED_PATTERNS),
        "opening_samples": opening_samples,
        "response_samples": response_samples,
        "side_effect_keys": list(SIDE_EFFECT_KEYS),
    }

    status = "PASS" if not failures else "FAIL"
    report_lines = [
        f"# {CHECKPOINT_ID}",
        "",
        f"Status: {status}",
        f"Scenarios: {result['scenario_count']}",
        f"Campaigns: {result['campaign_count']} total, {result['generic_campaign_count']} generic fixtures",
        f"Failures: {len(failures)}",
        "",
        "## Failure Types",
        *[f"- {name}: {count}" for name, count in sorted(failure_types.items())],
        "",
        "## Opening Samples",
        *[f"- {sample['campaign_id']}: {sample['response']}" for sample in opening_samples],
        "",
        "## Response Samples",
        *[
            f"- {sample['group']} / {sample['campaign_id']} / {sample['question']}: {sample['response']}"
            for sample in response_samples[:24]
        ],
        "",
        "## Side Effects",
        "- Provider calls, local LLM calls, email, calendar, CRM writes, PROD-102, live TTS, and audio-file creation must remain false.",
    ]
    write_evidence(result, "\n".join(report_lines) + "\n")
    print(f"{CHECKPOINT_ID}: {status} ({result['scenario_count']} scenarios, {len(failures)} failures)")
    if failures:
        for item in failures[:20]:
            print(json.dumps(item, sort_keys=True))
        print(f"Wrote evidence to {RESULT_PATH.relative_to(ROOT)}")
        return 1
    print(f"Wrote evidence to {RESULT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
