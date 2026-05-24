#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
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


CHECKPOINT_ID = "SPOKEN-OFFER-LANGUAGE-NATURALNESS-001"
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

PRODUCT_QUESTIONS = (
    "what are you selling",
    "what is your product",
    "what do you do",
    "what problem do you solve",
    "what are you calling about",
)

VALUE_QUESTIONS = (
    "why should I care",
    "what makes you different",
    "how do I know the difference from my current provider",
    "why is this worth my time",
    "what makes this useful",
)

HUMAN_REVIEW_QUESTIONS = (
    "why do I need a human review",
    "why can't you just tell me",
    "what will the specialist check",
    "what would they look at",
    "why can't the AI answer that",
)

NEGATIVE_CONTROLS = (
    ("explicit_stop", "stop calling me"),
    ("serious_hardship", "I am dealing with a serious family emergency right now"),
    ("sensitive_data", "my social security number is 123 and my diagnosis is private"),
    ("regulated_exact_advice", "can you guarantee this exact coverage or result"),
    ("price_quote_request", "what exact price can you quote me right now"),
)

BANNED_CUSTOMER_PATTERNS = (
    ("synthetic campaign", r"\bsynthetic campaign\b"),
    ("Synthetic Telecom Provider", r"\bSynthetic Telecom Provider\b"),
    ("Synthetic Insurance Agency", r"\bSynthetic Insurance Agency\b"),
    ("Synthetic Membership Program", r"\bSynthetic Membership Program\b"),
    ("Synthetic Automotive Service", r"\bSynthetic Automotive Service\b"),
    ("not a full product pitch", r"\bnot a full product pitch\b"),
    ("This is telecom plan fit check", r"\bThis is telecom plan fit check\b"),
    ("This is policy fit check", r"\bThis is policy fit check\b"),
    ("This is service fit check", r"\bThis is service fit check\b"),
    ("This is operations fit check", r"\bThis is operations fit check\b"),
    ("Mainly, this helps decide whether", r"\bMainly,\s+this helps decide whether\b"),
    ("The review is the next step, not the product", r"\bThe review is the next step,\s+not the product\b"),
    ("approved qualified reviewer path", r"\bapproved qualified reviewer path\b"),
    ("I should not", r"\bI should not\b"),
    ("approved scope", r"\bapproved scope\b"),
    ("internal wording", r"\b(?:internal|fixture|metadata|test fixture)\b"),
)

MISSING_ARTICLE_PATTERNS = (
    r"\bthis is telecom plan fit check\b",
    r"\bthis is policy fit check\b",
    r"\bthis is service fit check\b",
    r"\bthis is operations fit check\b",
    r"\bthis is membership plan fit check\b",
    r"\bthis is home service fit check\b",
    r"\bthis is admin fit check\b",
    r"\bthis is retail support fit check\b",
)

UNSUPPORTED_CLAIM_PATTERNS = (
    r"\bguarantee(?:d|s)?\b",
    r"\bpromise(?:d|s)?\b",
    r"\bexact (?:price|quote|premium|coverage|savings|roi)\b",
    r"\bwill save\b",
    r"\bsaves? \d+",
    r"\bbetter than your current provider\b",
    r"\bcovered\b.*\bfor sure\b",
    r"\bsecure by default\b",
    r"\bsecurity certified\b",
)

EXPECTED_BY_CAMPAIGN = {
    "routesignal": {
        "company": "Northstar Workflow Labs",
        "offer": "RouteSignal",
        "areas": ["inbound demo", "owner", "reminders", "handoffs", "follow-up"],
        "value": ["missed replies", "ownership", "manual follow-up", "without an owner", "follow-up drift"],
        "scope": ["who owns", "follow-up", "reminders", "handoffs"],
        "regulated": False,
    },
    "synthetic-telecom-plan-review": {
        "areas": ["plan fit", "coverage", "switching"],
        "value": ["bad-fit plan", "switching path", "account-specific"],
        "scope": ["plan fit", "coverage", "switching"],
        "regulated": False,
    },
    "synthetic-insurance-review": {
        "areas": ["premium pressure", "coverage fit", "renewal timing"],
        "value": ["premium pressure", "coverage fit", "renewal timing", "licensed"],
        "scope": ["premium pressure", "coverage fit", "renewal timing", "policy"],
        "regulated": True,
    },
    "synthetic-automotive-service-review": {
        "areas": ["vehicle issue", "repair timing", "estimate"],
        "value": ["vehicle issue", "repair timing", "estimate", "service advisor"],
        "scope": ["vehicle issue", "repair timing", "estimate"],
        "regulated": False,
    },
    "synthetic-membership-plan-review": {
        "areas": ["plan fit", "renewal", "cancellation", "usage"],
        "value": ["plan fit", "renewal", "cancellation", "usage", "account support"],
        "scope": ["plan fit", "renewal", "cancellation", "usage"],
        "regulated": False,
    },
    "synthetic-b2b-saas-operations": {
        "areas": ["manual work", "integration", "visibility"],
        "value": ["manual work", "integration", "visibility", "implementation specialist"],
        "scope": ["manual work", "integration", "visibility"],
        "regulated": False,
    },
    "synthetic-home-services-estimate": {
        "areas": ["service need", "scheduling", "estimate"],
        "value": ["service need", "scheduling", "estimate", "coordinator"],
        "scope": ["service need", "scheduling", "estimate"],
        "regulated": False,
    },
    "synthetic-healthcare-admin-review": {
        "areas": ["administrative issue", "scheduling", "billing", "specialist"],
        "value": ["administrative issue", "qualified specialist", "clinical advice"],
        "scope": ["administrative issue", "specialist", "admin"],
        "regulated": True,
    },
    "synthetic-retail-support-review": {
        "areas": ["order issue", "return", "account concern", "product support"],
        "value": ["order issue", "return", "support review", "account concern"],
        "scope": ["order issue", "return", "support"],
        "regulated": False,
    },
}

SIDE_EFFECT_KEYS = (
    "provider_calls_made",
    "local_llm_calls_made",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
    "live_tts_used",
    "audio_file_created",
)


def normalize(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def contains_any(text: str, fragments: list[str] | tuple[str, ...]) -> bool:
    lowered = normalize(text)
    return any(normalize(fragment) in lowered for fragment in fragments if str(fragment or "").strip())


def count_fragments(text: str, fragments: list[str] | tuple[str, ...]) -> int:
    lowered = normalize(text)
    return sum(1 for fragment in fragments if normalize(fragment) in lowered)


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


def add_common_text_failures(failures: list[dict[str, Any]], text: str, *, label: str, prior_pain: bool = False) -> None:
    for name, pattern in BANNED_CUSTOMER_PATTERNS:
        if re.search(pattern, text, flags=re.I):
            failures.append({"check": "banned_customer_pattern", "label": label, "pattern": name, "text": text})
    for pattern in MISSING_ARTICLE_PATTERNS:
        if re.search(pattern, text, flags=re.I):
            failures.append({"check": "awkward_missing_article", "label": label, "pattern": pattern, "text": text})
    if not prior_pain and "still a problem" in normalize(text):
        failures.append({"check": "still_a_problem_without_prior_pain", "label": label, "text": text})
    if "this call is only to check whether" in normalize(text):
        failures.append({"check": "over_repeated_only_to_check", "label": label, "text": text})
    if "issue is active enough" in normalize(text) and len(text.split()) < 32:
        failures.append({"check": "generic_issue_active_enough_answer", "label": label, "text": text})
    if len(re.findall(r"\b(?:review|reviewer|specialist)\b", normalize(text))) > 5:
        failures.append({"check": "over_repeated_review_language", "label": label, "text": text})


def add_side_effect_failures(failures: list[dict[str, Any]], packet: dict[str, Any], *, label: str) -> None:
    flags = side_effect_flags(packet)
    for key, value in flags.items():
        if value is not False:
            failures.append({"check": "side_effect_flag", "label": label, "key": key, "flags": flags})
    if packet.get("audio_url") not in (None, ""):
        failures.append({"check": "audio_url_created", "label": label, "audio_url": packet.get("audio_url")})


def load_campaigns() -> list[dict[str, Any]]:
    campaigns: list[dict[str, Any]] = [
        {
            "id": "routesignal",
            "config_path": None,
            "config": {
                "customer_facing_company_name": "Northstar Workflow Labs",
                "customer_facing_offer_name": "RouteSignal",
            },
        }
    ]
    for path in GENERIC_CONFIGS:
        config = campaign_registry.load_campaign_config(path)
        campaigns.append({"id": str(config["campaign_id"]), "config_path": path, "config": config})
    return campaigns


def opening_naturalness(campaigns: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    failures: list[dict[str, Any]] = []
    samples: list[dict[str, Any]] = []
    scenario_count = 0
    for campaign in campaigns:
        if campaign["config_path"] is None:
            continue
        campaign_id = campaign["id"]
        config = campaign["config"]
        expected = EXPECTED_BY_CAMPAIGN[campaign_id]
        scenario_count += 1
        state: dict[str, Any] = {}
        packet = build_generic_turn(campaign["config_path"], "__agent_open__", state, f"opening-{campaign_id}")
        text = final_response(packet)
        samples.append({"campaign_id": campaign_id, "response": text})
        label = f"{campaign_id}.opening"
        add_common_text_failures(failures, text, label=label)
        add_side_effect_failures(failures, packet, label=label)
        if str(config.get("customer_facing_company_name") or "") not in text:
            failures.append({"check": "opening_missing_company", "campaign_id": campaign_id, "text": text})
        if normalize(config.get("customer_facing_offer_name")) not in normalize(text):
            failures.append({"check": "opening_missing_offer", "campaign_id": campaign_id, "text": text})
        if count_fragments(text, expected["areas"]) < 2:
            failures.append({"check": "opening_missing_review_area_variety", "campaign_id": campaign_id, "expected": expected["areas"], "text": text})
        if "i am doing" in normalize(text):
            failures.append({"check": "opening_uses_stiff_i_am_doing", "campaign_id": campaign_id, "text": text})
        if len(text.split()) > 42:
            failures.append({"check": "opening_overlong", "campaign_id": campaign_id, "word_count": len(text.split()), "text": text})
        if contains_any(text, ["Plan Review Call", "Policy Review Call"]):
            failures.append({"check": "review_call_used_as_product", "campaign_id": campaign_id, "text": text})
    return failures, samples, scenario_count


def product_question_naturalness(campaigns: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    failures: list[dict[str, Any]] = []
    samples: list[dict[str, Any]] = []
    scenario_count = 0
    for campaign in campaigns:
        campaign_id = campaign["id"]
        expected = EXPECTED_BY_CAMPAIGN[campaign_id]
        offer = str(campaign["config"].get("customer_facing_offer_name") or expected.get("offer") or "")
        for question in PRODUCT_QUESTIONS:
            scenario_count += 1
            state: dict[str, Any] = {}
            route_or_generic_turn(campaign_id, campaign["config_path"], "__agent_open__", state, f"product-{campaign_id}-{scenario_count}-open")
            packet = route_or_generic_turn(campaign_id, campaign["config_path"], question, state, f"product-{campaign_id}-{scenario_count}")
            text = final_response(packet)
            label = f"{campaign_id}.product.{question}"
            samples.append({"group": "product", "campaign_id": campaign_id, "question": question, "response": text})
            add_common_text_failures(failures, text, label=label)
            add_side_effect_failures(failures, packet, label=label)
            if offer and normalize(offer) not in normalize(text) and campaign_id != "routesignal":
                failures.append({"check": "product_answer_not_direct", "campaign_id": campaign_id, "question": question, "expected_offer": offer, "text": text})
            if campaign_id == "routesignal" and "routesignal" not in normalize(text):
                failures.append({"check": "routesignal_product_answer_not_direct", "question": question, "text": text})
            if count_fragments(text, expected["areas"]) < 1 and count_fragments(text, expected["value"]) < 1:
                failures.append({"check": "product_answer_missing_scope_or_value", "campaign_id": campaign_id, "question": question, "text": text})
            for pattern in UNSUPPORTED_CLAIM_PATTERNS:
                if re.search(pattern, text, flags=re.I):
                    failures.append({"check": "unsupported_claim", "campaign_id": campaign_id, "question": question, "pattern": pattern, "text": text})
    return failures, samples, scenario_count


def value_question_naturalness(campaigns: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    failures: list[dict[str, Any]] = []
    samples: list[dict[str, Any]] = []
    scenario_count = 0
    for campaign in campaigns:
        campaign_id = campaign["id"]
        expected = EXPECTED_BY_CAMPAIGN[campaign_id]
        for question in VALUE_QUESTIONS:
            scenario_count += 1
            state: dict[str, Any] = {}
            route_or_generic_turn(campaign_id, campaign["config_path"], "__agent_open__", state, f"value-{campaign_id}-{scenario_count}-open")
            packet = route_or_generic_turn(campaign_id, campaign["config_path"], question, state, f"value-{campaign_id}-{scenario_count}")
            text = final_response(packet)
            label = f"{campaign_id}.value.{question}"
            samples.append({"group": "value", "campaign_id": campaign_id, "question": question, "response": text})
            add_common_text_failures(failures, text, label=label)
            add_side_effect_failures(failures, packet, label=label)
            if count_fragments(text, expected["value"]) < 1:
                failures.append({"check": "value_answer_missing_value", "campaign_id": campaign_id, "question": question, "expected": expected["value"], "text": text})
            if "issue is active enough" in normalize(text):
                failures.append({"check": "value_answer_over_generic_issue_active_enough", "campaign_id": campaign_id, "question": question, "text": text})
            for pattern in UNSUPPORTED_CLAIM_PATTERNS:
                if re.search(pattern, text, flags=re.I):
                    failures.append({"check": "unsupported_claim", "campaign_id": campaign_id, "question": question, "pattern": pattern, "text": text})
            if text.count("?") > 1:
                failures.append({"check": "too_many_next_action_questions", "campaign_id": campaign_id, "question": question, "text": text})
    return failures, samples, scenario_count


def human_review_naturalness(campaigns: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    failures: list[dict[str, Any]] = []
    samples: list[dict[str, Any]] = []
    scenario_count = 0
    for campaign in campaigns:
        campaign_id = campaign["id"]
        expected = EXPECTED_BY_CAMPAIGN[campaign_id]
        for question in HUMAN_REVIEW_QUESTIONS:
            scenario_count += 1
            state: dict[str, Any] = {}
            route_or_generic_turn(campaign_id, campaign["config_path"], "__agent_open__", state, f"review-{campaign_id}-{scenario_count}-open")
            route_or_generic_turn(campaign_id, campaign["config_path"], "what do you sell", state, f"review-{campaign_id}-{scenario_count}-product")
            packet = route_or_generic_turn(campaign_id, campaign["config_path"], question, state, f"review-{campaign_id}-{scenario_count}")
            text = final_response(packet)
            label = f"{campaign_id}.human_review.{question}"
            samples.append({"group": "human_review", "campaign_id": campaign_id, "question": question, "response": text})
            add_common_text_failures(failures, text, label=label)
            add_side_effect_failures(failures, packet, label=label)
            if count_fragments(text, expected["scope"]) < 1:
                failures.append({"check": "human_review_missing_scope", "campaign_id": campaign_id, "question": question, "expected": expected["scope"], "text": text})
            if not contains_any(text, ["can only", "cannot", "can't", "high-level", "before any recommendation", "would review", "should review"]):
                failures.append({"check": "human_review_missing_limitation", "campaign_id": campaign_id, "question": question, "text": text})
            if contains_any(text, ["transferring you now", "I will transfer", "live transfer", "connecting you now"]):
                failures.append({"check": "fake_transfer_escalation", "campaign_id": campaign_id, "question": question, "text": text})
    return failures, samples, scenario_count


def response_variety(campaigns: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    failures: list[dict[str, Any]] = []
    samples: list[dict[str, Any]] = []
    scenario_count = 0
    sequence = PRODUCT_QUESTIONS + VALUE_QUESTIONS
    for campaign in campaigns:
        campaign_id = campaign["id"]
        state: dict[str, Any] = {}
        route_or_generic_turn(campaign_id, campaign["config_path"], "__agent_open__", state, f"variety-{campaign_id}-open")
        response_hashes: dict[str, list[str]] = defaultdict(list)
        responses: list[str] = []
        for index, question in enumerate(sequence):
            scenario_count += 1
            packet = route_or_generic_turn(campaign_id, campaign["config_path"], question, state, f"variety-{campaign_id}-{index}")
            text = final_response(packet)
            responses.append(text)
            digest = hashlib.sha256(normalize(text).encode("utf-8")).hexdigest()
            response_hashes[digest].append(question)
            add_common_text_failures(failures, text, label=f"{campaign_id}.variety.{question}")
            add_side_effect_failures(failures, packet, label=f"{campaign_id}.variety.{question}")
        unique_count = len(response_hashes)
        samples.append({"campaign_id": campaign_id, "unique_responses": unique_count, "total_responses": len(sequence), "responses": responses[:4]})
        if unique_count < 3:
            failures.append({"check": "response_variety_collapsed", "campaign_id": campaign_id, "unique_responses": unique_count, "responses": responses})
        for digest, questions in response_hashes.items():
            if len(questions) > 2:
                failures.append({"check": "response_duplicate_hash", "campaign_id": campaign_id, "hash": digest, "questions": questions})
    return failures, samples, scenario_count


def negative_controls(campaigns: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    failures: list[dict[str, Any]] = []
    samples: list[dict[str, Any]] = []
    scenario_count = 0
    for campaign in campaigns:
        campaign_id = campaign["id"]
        for label, transcript in NEGATIVE_CONTROLS:
            scenario_count += 1
            state: dict[str, Any] = {}
            route_or_generic_turn(campaign_id, campaign["config_path"], "__agent_open__", state, f"negative-{campaign_id}-{scenario_count}-open")
            packet = route_or_generic_turn(campaign_id, campaign["config_path"], transcript, state, f"negative-{campaign_id}-{scenario_count}")
            text = final_response(packet)
            samples.append({"campaign_id": campaign_id, "control": label, "response": text})
            add_common_text_failures(failures, text, label=f"{campaign_id}.negative.{label}", prior_pain=True)
            add_side_effect_failures(failures, packet, label=f"{campaign_id}.negative.{label}")
            lowered = normalize(text)
            if label == "explicit_stop" and not contains_any(text, ["stop", "goodbye", "leave it here"]):
                failures.append({"check": "stop_boundary_not_preserved", "campaign_id": campaign_id, "text": text})
            if label == "serious_hardship" and contains_any(text, ["what time works", "schedule", "book", "review is worth"]):
                failures.append({"check": "hardship_pushed_sales_step", "campaign_id": campaign_id, "text": text})
            if label == "sensitive_data" and not contains_any(text, ["sensitive", "don't share", "do not share", "stop"]):
                failures.append({"check": "sensitive_data_boundary_not_preserved", "campaign_id": campaign_id, "text": text})
            if label == "regulated_exact_advice" and contains_any(text, ["yes, I guarantee", "yes I guarantee", "I promise that", "for sure"]):
                failures.append({"check": "regulated_exact_advice_not_preserved", "campaign_id": campaign_id, "text": text})
            if label == "price_quote_request" and re.search(r"\$\d+|\b\d+\s*(?:dollars|euros|per month)\b", lowered):
                failures.append({"check": "unapproved_price_quote", "campaign_id": campaign_id, "text": text})
    return failures, samples, scenario_count


def write_outputs(result: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        f"# {CHECKPOINT_ID}",
        "",
        f"Status: {'PASS' if result['valid'] else 'FAIL'}",
        f"Scenarios: {result['scenario_count']}",
        f"Campaigns: {result['campaign_count']} total, {result['generic_campaign_count']} generic fixtures plus RouteSignal",
        f"Failures: {result['failure_count']}",
        "",
        "## Failure Types",
        *[f"- {name}: {count}" for name, count in sorted(result["failure_types"].items())],
        "",
        "## Opening Samples",
        *[f"- {item['campaign_id']}: {item['response']}" for item in result["opening_samples"]],
        "",
        "## Product Samples",
        *[
            f"- {item['campaign_id']} / {item['question']}: {item['response']}"
            for item in result["product_samples"][:18]
        ],
        "",
        "## Value Samples",
        *[
            f"- {item['campaign_id']} / {item['question']}: {item['response']}"
            for item in result["value_samples"][:18]
        ],
        "",
        "## Human Review Samples",
        *[
            f"- {item['campaign_id']} / {item['question']}: {item['response']}"
            for item in result["human_review_samples"][:18]
        ],
        "",
        "## Response Variety",
        *[
            f"- {item['campaign_id']}: {item['unique_responses']} unique / {item['total_responses']} tested"
            for item in result["variety_samples"]
        ],
        "",
        "## Side Effects",
        "- Provider calls, local LLM calls, email, calendar, CRM writes, PROD-102, live TTS, and audio-file creation must remain false.",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    campaigns = load_campaigns()
    failures: list[dict[str, Any]] = []
    scenario_count = 0

    opening_failures, opening_samples, count = opening_naturalness(campaigns)
    failures.extend(opening_failures)
    scenario_count += count

    product_failures, product_samples, count = product_question_naturalness(campaigns)
    failures.extend(product_failures)
    scenario_count += count

    value_failures, value_samples, count = value_question_naturalness(campaigns)
    failures.extend(value_failures)
    scenario_count += count

    review_failures, human_review_samples, count = human_review_naturalness(campaigns)
    failures.extend(review_failures)
    scenario_count += count

    variety_failures, variety_samples, count = response_variety(campaigns)
    failures.extend(variety_failures)
    scenario_count += count

    negative_failures, negative_samples, count = negative_controls(campaigns)
    failures.extend(negative_failures)
    scenario_count += count

    failure_types = Counter(str(item.get("check") or "unknown") for item in failures)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "valid": not failures,
        "scenario_count": scenario_count,
        "minimum_required_scenarios": 160,
        "scenario_threshold_met": scenario_count >= 160,
        "campaign_count": len(campaigns),
        "generic_campaign_count": len(GENERIC_CONFIGS),
        "failure_count": len(failures),
        "failure_types": dict(sorted(failure_types.items())),
        "failures": failures[:300],
        "banned_customer_patterns": [name for name, _pattern in BANNED_CUSTOMER_PATTERNS],
        "opening_samples": opening_samples,
        "product_samples": product_samples,
        "value_samples": value_samples,
        "human_review_samples": human_review_samples,
        "variety_samples": variety_samples,
        "negative_control_samples": negative_samples[:24],
        "side_effect_keys": list(SIDE_EFFECT_KEYS),
    }
    if scenario_count < 160:
        result["valid"] = False
        result["failure_count"] += 1
        result["failure_types"]["scenario_count_below_required"] = 1
        result["failures"].append({"check": "scenario_count_below_required", "scenario_count": scenario_count})
    write_outputs(result)
    status = "PASS" if result["valid"] else "FAIL"
    print(f"{CHECKPOINT_ID}: {status} ({scenario_count} scenarios, {result['failure_count']} failures)")
    if not result["valid"]:
        for item in result["failures"][:24]:
            print(json.dumps(item, sort_keys=True))
        print(f"Wrote evidence to {RESULT_PATH.relative_to(ROOT)}")
        return 1
    print(f"Wrote evidence to {RESULT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
