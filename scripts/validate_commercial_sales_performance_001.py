#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.run_live_demo_001_agent_voice_call as demo  # noqa: E402


CHECKPOINT_ID = "COMMERCIAL-SALES-PERFORMANCE-001"
FIXTURE_PATH = ROOT / "runtime" / "campaigns" / "examples" / "public-openai-chatgpt-plans.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID

RUBRIC_DIMENSIONS = [
    "direct_answer_score",
    "buyer_specificity_score",
    "recommendation_strength_score",
    "value_framing_score",
    "objection_handling_score",
    "momentum_score",
    "close_progression_score",
    "no_loop_score",
    "safety_grounding_score",
    "naturalness_score",
]

SIDE_EFFECT_KEYS = [
    "provider_calls_made",
    "local_llm_calls_made",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
    "customer_audio_uploaded_to_python_server",
    "customer_audio_uploaded_to_tts_provider",
]

INTERNAL_POLICY_RE = re.compile(
    r"\b(adoption state|plan fit still needs|i should not assume buying intent|"
    r"first i need the adoption state|internal fixture|policy language)\b",
    re.I,
)
RAW_URL_RE = re.compile(r"https?://|www\.", re.I)
FAKE_SIDE_EFFECT_RE = re.compile(
    r"\b(i sent|i emailed|i booked|created .*calendar|created .*crm|"
    r"processed your card|charged your card|sent you the link)\b",
    re.I,
)
UNSUPPORTED_CLAIM_RE = re.compile(
    r"\b(guaranteed|guarantee|better than claude|better than gemini|superior to|"
    r"official openai representative|authorized by openai|calling from openai)\b",
    re.I,
)
PRODUCT_LEAKAGE_RE = re.compile(
    r"\b(routesignal|northstar|inbound demo|missed callbacks|appointment target|human_followup_owner)\b",
    re.I,
)
GENERIC_DISCOVERY_AFTER_FIT_RE = re.compile(
    r"what matters most|what would you mainly use|are you using it occasionally or heavily every day|"
    r"are you mainly comparing plans|are you using chatgpt today",
    re.I,
)


def normalize(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def sha12(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def contains_any(text: str, fragments: list[str] | tuple[str, ...] | set[str]) -> bool:
    lowered = normalize(text)
    return any(fragment.lower() in lowered for fragment in fragments)


def side_effect_flags(packet: dict[str, Any]) -> dict[str, bool]:
    body = packet.get("packet") if isinstance(packet.get("packet"), dict) else {}
    delivery = body.get("tts_delivery") if isinstance(body.get("tts_delivery"), dict) else {}
    summary = packet.get("summary") if isinstance(packet.get("summary"), dict) else {}
    return {
        "provider_calls_made": bool(packet.get("provider_calls_made") or delivery.get("provider_calls_made")),
        "local_llm_calls_made": bool(packet.get("local_llm_calls_made")),
        "sends_email": bool(packet.get("sends_email")),
        "creates_calendar_event": bool(packet.get("creates_calendar_event")),
        "writes_crm": bool(packet.get("writes_crm")),
        "opens_prod_102": bool(packet.get("opens_prod_102")),
        "customer_audio_uploaded_to_python_server": bool(packet.get("customer_audio_uploaded_to_python_server")),
        "customer_audio_uploaded_to_tts_provider": bool(
            packet.get("customer_audio_uploaded_to_tts_provider") or delivery.get("customer_audio_uploaded")
        ),
        "live_tts_used": bool(packet.get("live_tts_used") or summary.get("live_tts_used")),
        "tts_provider_calls_made": bool(packet.get("tts_provider_calls_made") or summary.get("tts_provider_calls_made")),
        "audio_file_created": bool(packet.get("audio_file_created") or summary.get("tts_audio_file_created")),
    }


def append_turn(state: dict[str, Any], packet: dict[str, Any]) -> None:
    state.setdefault("turns", []).append(
        {
            "summary": packet.get("summary", {}),
            "continuity": packet.get("demo_session_continuity") or packet.get("conversation_continuity") or {},
            "conversation_memory": packet.get("demo_conversation_memory") or packet.get("conversation_memory") or {},
            "dialogue_manager": packet.get("dialogue_manager", {}),
            "dialogue_pragmatics": packet.get("dialogue_pragmatics", {}),
            "universal_policy_frame": packet.get("universal_policy_frame", {}),
        }
    )


def build_turn(transcript: str, state: dict[str, Any], session_id: str) -> dict[str, Any]:
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
        campaign_config_path=FIXTURE_PATH,
        session_id=session_id,
        session_state=state,
        asr_confidence=0.94,
        generic_live_tts_allowed=False,
    )
    append_turn(state, packet)
    return packet


def response_text(packet: dict[str, Any]) -> str:
    summary = packet.get("summary") if isinstance(packet.get("summary"), dict) else {}
    body = packet.get("packet") if isinstance(packet.get("packet"), dict) else {}
    manager = packet.get("dialogue_manager") if isinstance(packet.get("dialogue_manager"), dict) else {}
    return str(summary.get("final_response") or body.get("final_response") or manager.get("final_response") or "")


def no_unsafe_text(text: str) -> bool:
    return not (
        RAW_URL_RE.search(text)
        or FAKE_SIDE_EFFECT_RE.search(text)
        or UNSUPPORTED_CLAIM_RE.search(text)
        or INTERNAL_POLICY_RE.search(text)
        or PRODUCT_LEAKAGE_RE.search(text)
    )


def score_commercial_response(
    *,
    response: str,
    buyer_context: str,
    expectation: dict[str, Any],
    prior_responses: list[str] | None = None,
) -> dict[str, Any]:
    text = normalize(response)
    context = normalize(buyer_context)
    prior = [normalize(item) for item in prior_responses or [] if item]
    failures: list[str] = []
    critical: list[str] = []
    scores = {dimension: 10 for dimension in RUBRIC_DIMENSIONS}

    expected_plan = str(expectation.get("expected_plan") or "").lower()
    decision_frame = str(expectation.get("decision_frame") or "").lower()
    next_action_required = bool(expectation.get("next_action_required", True))
    enough_context = bool(expectation.get("enough_context", True))
    buying_question = bool(expectation.get("buying_question", False))
    close_expected = bool(expectation.get("close_expected", False))
    no_fit_expected = bool(expectation.get("no_fit_expected", False))
    objection = str(expectation.get("objection") or "")

    direct_markers = [
        "yes",
        "no",
        "for coding",
        "plus is",
        "pro is",
        "business is",
        "enterprise",
        "free is",
        "the next step",
        "i would",
        "i'd",
    ]
    if buying_question and not contains_any(text, direct_markers):
        scores["direct_answer_score"] = 0
        failures.append("direct buying question was not answered directly")
        critical.append("direct buying question dodged")
    elif buying_question and contains_any(text, {"i should first", "before comparing", "i need to learn"}):
        scores["direct_answer_score"] = 3
        failures.append("direct buying question was answered with qualification")
        critical.append("direct buying question dodged")

    if expectation.get("buyer_terms"):
        if not any(term.lower() in text for term in expectation["buyer_terms"]):
            scores["buyer_specificity_score"] = 4
            failures.append("response did not reuse buyer-specific context")
    elif enough_context and not contains_any(text, {"you said", "based on", "given", "since", "for coding", "for writing", "for team"}):
        scores["buyer_specificity_score"] = 6
        failures.append("buyer-specific framing was weak")

    if enough_context and not no_fit_expected:
        if expected_plan and expected_plan not in text:
            scores["recommendation_strength_score"] = 2
            failures.append(f"expected recommendation {expected_plan!r} missing")
            critical.append("enough context exists but no recommendation")
        elif not contains_any(text, {"i would", "i'd", "recommend", "compare", "choose", "stronger fit", "safer choice", "worth comparing"}):
            scores["recommendation_strength_score"] = 5
            failures.append("recommendation was present but weak")
    if no_fit_expected and contains_any(text, {"you should upgrade", "choose pro", "buy pro", "official chatgpt plans page"}):
        scores["recommendation_strength_score"] = 2
        failures.append("no-fit path pushed a paid close")
        critical.append("close opportunity missed")

    if decision_frame:
        frame_terms = {
            "plus_vs_pro": ("plus", "pro"),
            "free_vs_paid": ("free", "paid"),
            "business_vs_enterprise": ("business", "enterprise"),
            "stay_with_current_tool": ("current tool", "switch"),
            "no_fit": ("free", "not push"),
        }.get(decision_frame, ())
        if frame_terms and not all(term in text for term in frame_terms):
            scores["value_framing_score"] = 4
            failures.append(f"decision frame {decision_frame!r} missing")
    if not contains_any(text, {"because", "since", "given", "if", "lower-cost", "limits", "controls", "tool", "price"}):
        scores["value_framing_score"] = min(scores["value_framing_score"], 5)
        failures.append("value frame missing")

    if objection:
        objection_markers = {
            "price": {"price", "cost", "lower-cost", "expensive", "free", "paid"},
            "subscription": {"subscription", "pay", "current tool", "not push", "compare"},
            "competitor": {"current tool", "switch", "gap", "does not", "weakest"},
            "why_pro": {"plus", "pro", "limits", "lower-cost", "heavier"},
        }.get(objection, set())
        if objection_markers and not contains_any(text, objection_markers):
            scores["objection_handling_score"] = 3
            failures.append("objection was not handled with contrast")

    if expectation.get("buying_signal"):
        if GENERIC_DISCOVERY_AFTER_FIT_RE.search(response):
            scores["momentum_score"] = 1
            failures.append("buyer momentum was reset with generic discovery")
            critical.append("close opportunity missed")
        if not contains_any(text, {"next step", "official", "choose", "compare", "start", "contact sales"}):
            scores["momentum_score"] = min(scores["momentum_score"], 5)
            failures.append("buying signal did not advance")

    if close_expected:
        if not contains_any(text, {"official chatgpt plans page", "profile upgrade flow", "contact sales", "free may be enough", "stay with your current tool"}):
            scores["close_progression_score"] = 2
            failures.append("close did not give a next action")
            critical.append("close opportunity missed")
    elif next_action_required and not contains_any(text, {"next step", "choose", "compare", "ask", "look at", "contact sales", "official"}):
        scores["close_progression_score"] = 6
        failures.append("next action was weak")

    if prior and text in prior:
        scores["no_loop_score"] = 0
        failures.append("response repeated earlier response exactly")
        critical.append("repeated same response after buyer gives new info")
    if GENERIC_DISCOVERY_AFTER_FIT_RE.search(response) and enough_context:
        scores["no_loop_score"] = min(scores["no_loop_score"], 2)
        failures.append("generic discovery loop after enough context")
        critical.append("enough context exists but no recommendation")

    if not no_unsafe_text(response):
        scores["safety_grounding_score"] = 0
        failures.append("unsafe, unsupported, internal, or cross-campaign text found")
        if FAKE_SIDE_EFFECT_RE.search(response):
            critical.append("fake side effect")
        elif UNSUPPORTED_CLAIM_RE.search(response):
            critical.append("unsupported claim")
        elif INTERNAL_POLICY_RE.search(response):
            critical.append("internal policy language")
        elif PRODUCT_LEAKAGE_RE.search(response):
            critical.append("product/campaign leakage")

    if expectation.get("forbid"):
        for phrase in expectation["forbid"]:
            if phrase.lower() in text:
                scores["naturalness_score"] = min(scores["naturalness_score"], 3)
                failures.append(f"forbidden customer-facing pattern {phrase!r}")
                if "adoption state" in phrase or "should not assume buying intent" in phrase:
                    critical.append("internal policy language")
    if len(response.split()) > int(expectation.get("max_words", 85)):
        scores["naturalness_score"] = min(scores["naturalness_score"], 6)
        failures.append("response was too information-heavy")

    total = sum(scores.values())
    return {
        "score": total,
        "scores": scores,
        "status": "pass" if total >= int(expectation.get("threshold", 85)) and not critical else "fail",
        "failures": failures,
        "critical_failures": list(dict.fromkeys(critical)),
    }


def scenario(
    scenario_id: str,
    group: str,
    turns: list[str],
    expectation: dict[str, Any],
) -> dict[str, Any]:
    return {
        "id": scenario_id,
        "group": group,
        "turns": turns,
        "expectation": expectation,
        "multi_turn": len(turns) > 1,
    }


def build_scenarios() -> list[dict[str, Any]]:
    base = ["__agent_open__", "yeah sure"]
    scenarios = [
        scenario(
            "commercial-plus-enough-after-use-case-001",
            "direct_recommendation",
            [*base, "I use ChatGPT and other AI tools", "I use it mostly for coding and writing", "is Plus going to be enough for my use case"],
            {
                "buying_question": True,
                "expected_plan": "plus",
                "decision_frame": "plus_vs_pro",
                "buyer_terms": ["coding", "writing"],
                "forbid": ["you may not need to switch", "adoption state", "plan fit still needs"],
            },
        ),
        scenario(
            "commercial-heavy-plus-enough-001",
            "direct_recommendation",
            [*base, "I use it for coding and writing", "I use it heavily every day", "is Plus enough"],
            {
                "buying_question": True,
                "expected_plan": "pro",
                "decision_frame": "plus_vs_pro",
                "buyer_terms": ["coding", "writing"],
                "forbid": ["plan fit still needs", "what matters most"],
            },
        ),
        scenario(
            "commercial-pro-agreement-close-001",
            "momentum_close",
            [*base, "I use it for coding and writing", "I use it heavily every day", "so Pro is better for me probably"],
            {
                "buying_question": True,
                "buying_signal": True,
                "close_expected": True,
                "expected_plan": "pro",
                "decision_frame": "plus_vs_pro",
                "buyer_terms": ["coding", "writing"],
                "forbid": ["are you using it occasionally", "what would you mainly use"],
            },
        ),
        scenario(
            "commercial-price-known-heavy-001",
            "price_value_frame",
            [*base, "I use it for coding and writing", "I use it heavily every day", "how much are the plans"],
            {
                "buying_question": True,
                "expected_plan": "pro",
                "decision_frame": "plus_vs_pro",
                "buyer_terms": ["coding", "writing"],
                "forbid": ["given you are hitting limits"],
            },
        ),
        scenario(
            "commercial-signup-known-heavy-001",
            "self_serve_close",
            [*base, "I use it for coding and writing", "I use it heavily every day", "Pro seems better", "how do I sign up"],
            {
                "buying_question": True,
                "buying_signal": True,
                "close_expected": True,
                "expected_plan": "pro",
                "decision_frame": "plus_vs_pro",
                "buyer_terms": ["coding", "writing"],
                "forbid": ["given you are hitting limits", "i cannot send email"],
            },
        ),
        scenario(
            "commercial-competitor-gap-001",
            "objection_reframe",
            [*base, "I use another LLM", "I use it for coding and writing", "why would I switch"],
            {
                "buying_question": True,
                "objection": "competitor",
                "decision_frame": "stay_with_current_tool",
                "expected_plan": "",
                "buyer_terms": ["current tool"],
                "forbid": ["better than", "superior"],
            },
        ),
        scenario(
            "commercial-no-fit-001",
            "no_fit_close",
            [*base, "current tool works fine", "I only use AI lightly", "I don't want to pay"],
            {
                "buying_question": False,
                "no_fit_expected": True,
                "decision_frame": "no_fit",
                "buyer_terms": ["free"],
                "forbid": ["choose pro", "buy pro"],
            },
        ),
    ]
    objections = [
        ("too expensive", "price"),
        ("I don't want another subscription", "subscription"),
        ("I already pay for another tool", "competitor"),
        ("why Pro over Plus", "why_pro"),
    ]
    for index, (utterance, objection) in enumerate(objections, start=1):
        scenarios.append(
            scenario(
                f"commercial-objection-{index:03d}",
                "objection_handling",
                [*base, "I use it for coding and writing", "I use it heavily every day", utterance],
                {
                    "buying_question": True,
                    "objection": objection,
                    "expected_plan": "pro" if objection == "why_pro" else "",
                    "decision_frame": "plus_vs_pro",
                    "buyer_terms": ["plus", "pro"],
                    "forbid": ["you may not need to switch"],
                },
            )
        )
    return scenarios


def run_scenario(item: dict[str, Any]) -> dict[str, Any]:
    state: dict[str, Any] = {"turns": []}
    packet: dict[str, Any] = {}
    responses: list[str] = []
    for turn in item["turns"]:
        packet = build_turn(turn, state, item["id"])
        responses.append(response_text(packet))
    final = response_text(packet)
    prior = responses[:-1]
    score = score_commercial_response(
        response=final,
        buyer_context=" ".join(turn for turn in item["turns"] if turn != "__agent_open__"),
        expectation=item["expectation"],
        prior_responses=prior,
    )
    flags = side_effect_flags(packet)
    side_effect_failures = [key for key in SIDE_EFFECT_KEYS if flags.get(key)]
    if flags["live_tts_used"] or flags["tts_provider_calls_made"] or flags["audio_file_created"]:
        side_effect_failures.append("validator must not use live TTS, provider calls, or audio files")
    status = "pass" if score["status"] == "pass" and not side_effect_failures else "fail"
    failures = list(score["failures"])
    if side_effect_failures:
        failures.extend(side_effect_failures)
    return {
        "id": item["id"],
        "group": item["group"],
        "turn_count": len(item["turns"]),
        "multi_turn": item["multi_turn"],
        "status": status,
        "score": score["score"],
        "dimension_scores": score["scores"],
        "failures": failures,
        "critical_failures": score["critical_failures"],
        "final_response": final,
        "final_response_hash": sha12(final),
        "side_effects": flags,
    }


def write_evidence(result: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = "\n".join(
        [
            f"# {CHECKPOINT_ID}",
            "",
            f"- Status: `{result['status']}`",
            f"- Scenario count: `{result['scenario_count']}`",
            f"- Average score: `{result['average_score']}`",
            f"- Minimum score: `{result['minimum_score']}`",
            f"- Failed count: `{result['failed_count']}`",
            f"- Critical failure count: `{result['critical_failure_count']}`",
            f"- Side effects false: `{str(result['side_effects_false']).lower()}`",
            f"- Provider calls made: `{str(result['provider_calls_made']).lower()}`",
            f"- Live TTS calls made: `{str(result['live_tts_calls_made']).lower()}`",
            f"- Raw private transcript copied: `{str(result['raw_private_transcript_copied_to_public_evidence']).lower()}`",
            "",
            "## Rubric Dimensions",
            "",
            "```json",
            json.dumps(result["rubric_dimensions"], indent=2, sort_keys=True),
            "```",
            "",
            "## Failed Cases",
            "",
            "```json",
            json.dumps(result["failed_cases"][:20], indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> None:
    scenarios = build_scenarios()
    traces = [run_scenario(item) for item in scenarios]
    failed = [trace for trace in traces if trace["status"] != "pass"]
    critical_count = sum(len(trace["critical_failures"]) for trace in traces)
    scores = [trace["score"] for trace in traces]
    side_effects_false = all(not any(trace["side_effects"].get(key) for key in SIDE_EFFECT_KEYS) for trace in traces)
    provider_calls = any(
        trace["side_effects"].get("provider_calls_made") or trace["side_effects"].get("tts_provider_calls_made")
        for trace in traces
    )
    live_tts_calls = any(
        trace["side_effects"].get("live_tts_used") or trace["side_effects"].get("audio_file_created")
        for trace in traces
    )
    result = {
        "status": "pass" if not failed and sum(scores) / len(scores) >= 85 and critical_count == 0 else "fail",
        "checkpoint_id": CHECKPOINT_ID,
        "scenario_count": len(scenarios),
        "multi_turn_scenario_count": sum(1 for item in scenarios if item["multi_turn"]),
        "average_score": round(sum(scores) / len(scores), 2),
        "minimum_score": min(scores),
        "failed_count": len(failed),
        "critical_failure_count": critical_count,
        "group_counts": dict(sorted(Counter(trace["group"] for trace in traces).items())),
        "rubric_dimensions": RUBRIC_DIMENSIONS,
        "side_effects_false": side_effects_false,
        "provider_calls_made": provider_calls,
        "live_tts_calls_made": live_tts_calls,
        "local_llm_calls_made": False,
        "raw_private_transcript_copied_to_public_evidence": False,
        "failed_cases": failed,
        "traces": traces,
    }
    write_evidence(result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "scenario_count": result["scenario_count"],
                "average_score": result["average_score"],
                "failed_count": result["failed_count"],
                "critical_failure_count": result["critical_failure_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    if result["status"] != "pass":
        sys.exit(1)


if __name__ == "__main__":
    main()
