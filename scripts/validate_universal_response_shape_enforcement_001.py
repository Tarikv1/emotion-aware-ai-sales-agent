"""Validate narrow universal response-shape enforcement.

This checkpoint covers only direct product/value questions, objections, and
early time-pressure permission. It runs dry-run turn builders and does not make
provider, live TTS, email, calendar, or CRM calls.
"""

from __future__ import annotations

from collections import defaultdict
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import run_live_demo_001_agent_voice_call as demo  # noqa: E402


CHECKPOINT_ID = "UNIVERSAL-RESPONSE-SHAPE-ENFORCEMENT-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID
EXAMPLES = ROOT / "runtime" / "campaigns" / "examples"

CAMPAIGNS = [
    {"id": "routesignal_live_demo", "config_path": None, "generic": False},
    {"id": "synthetic-insurance-review", "config_path": EXAMPLES / "synthetic-insurance-review.json", "generic": True},
    {"id": "synthetic-b2b-saas-operations", "config_path": EXAMPLES / "synthetic-b2b-saas-operations.json", "generic": True},
    {"id": "synthetic-automotive-service-review", "config_path": EXAMPLES / "synthetic-automotive-service-review.json", "generic": True},
    {"id": "synthetic-home-services-estimate", "config_path": EXAMPLES / "synthetic-home-services-estimate.json", "generic": True},
]

DIRECT_QUESTION_CASES = [
    ("what does your product do", "product_detail_question"),
    ("what problem do you solve", "what_problem_do_you_solve"),
    ("why should I care", "why_should_i_care"),
    ("what makes you different", "what_makes_you_different"),
    ("who is this for", "who_is_this_for"),
    ("is this worth my time", "is_this_worth_my_time"),
]

OBJECTION_CASES = [
    ("we already have a provider", "already_has_provider"),
    ("too expensive", "price_or_budget_objection"),
    ("I need to ask my manager", "no_authority_or_needs_approval"),
    ("send me proof", "wants_proof_or_case_study"),
    ("not this week", "timing_objection"),
    ("I do not see the need", "no_clear_need"),
    ("we are too busy", "too_busy_now"),
]

TIME_PRESSURE_CASES = [
    ("make it quick", "time_constrained_permission"),
    ("just a short minute", "time_constrained_permission"),
]

GENERIC_ROUTE_SIGNAL_LEAKS = [
    "routesignal",
    "northstar",
    "starter",
    "growth",
    "$29",
    "$59",
    "inbound-demo",
    "demo-follow-up",
    "missed-callbacks",
    "manual-tracking",
    "messy-handoffs",
]

INTERNAL_PATTERNS = [
    "i should",
    "approved qualified reviewer path",
    "internal policy",
    "i am asking whether",
    "if premium or budget, coverage fit, or renewal or timing are actually relevant",
    "if vehicle issue, repair timing, or warranty or estimate are actually relevant",
]

UNSAFE_CLAIM_PATTERNS = [
    "we guarantee",
    "i guarantee",
    "can guarantee",
    "will guarantee",
    "guaranteed result",
    "promise the result",
    "promise coverage",
    "exact price is",
    "exact quote is",
    "covered for sure",
    "roi guarantee",
    "revenue guarantee",
    "security guarantee",
    "case study shows",
]

FULL_MENU_PATTERNS = [
    "owner, callback reminder, or handoff",
    "assignment, reminders, or missed replies",
    "premium, coverage fit, or renewal",
    "premium or budget, coverage fit, or renewal",
    "manual work, integration, or visibility",
    "vehicle issue, repair timing, or warranty",
    "service need, scheduling, or estimate",
]

APPOINTMENT_PRESSURE_PATTERNS = [
    "what time works",
    "what time should",
    "note a time",
    "book",
    "schedule",
    "appointment",
]


def append_turn(state: dict[str, Any], packet: dict[str, Any]) -> None:
    summary = packet.get("summary") or {}
    state.setdefault("turns", []).append(
        {
            "transcript": packet.get("transcript") or "",
            "summary": summary,
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


def run_sequence(campaign: dict[str, Any], transcript: str, context: str, index: int) -> dict[str, Any]:
    session_id = f"{index:03d}-{campaign['id']}-{slug(transcript)}"[:120]
    state: dict[str, Any] = {}
    turns = ["__agent_open__"]
    if context == "after_permission":
        turns.append("yeah sure")
    turns.append(transcript)
    packet: dict[str, Any] = {}
    for turn in turns:
        packet = build_turn(turn, state, campaign, session_id)
    return packet


def slug(text: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in text.lower()).strip("-")


def final_response(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("final_response") or packet.get("final_response") or "")


def lower_response(packet: dict[str, Any]) -> str:
    return final_response(packet).lower()


def frame(packet: dict[str, Any]) -> dict[str, Any]:
    return packet.get("universal_policy_frame") or (packet.get("dialogue_manager") or {}).get("universal_policy_frame") or {}


def call_control(packet: dict[str, Any]) -> str:
    return str((packet.get("summary") or {}).get("call_control") or (packet.get("dialogue_manager") or {}).get("call_control") or "")


def source(packet: dict[str, Any]) -> str:
    manager = packet.get("dialogue_manager") or {}
    selected = manager.get("selected_action") or {}
    return str(selected.get("source") or "")


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


def has_any(text: str, patterns: list[str]) -> bool:
    return any(pattern in text for pattern in patterns)


def evaluate_common(
    *,
    packet: dict[str, Any],
    campaign: dict[str, Any],
    expected_move: str,
    category: str,
) -> list[str]:
    failures: list[str] = []
    response = lower_response(packet)
    policy = frame(packet)
    if policy.get("buyer_move_id") != expected_move:
        failures.append(f"expected buyer_move_id {expected_move}, got {policy.get('buyer_move_id')}")
    if policy.get("recognition_confidence") != "high":
        failures.append(f"expected high recognition confidence, got {policy.get('recognition_confidence')}")
    if policy.get("response_shape_enforcement_enabled") is not True:
        failures.append("response shape enforcement was not enabled")
    if policy.get("response_shape_enforced_category") != category:
        failures.append(f"expected enforced category {category}, got {policy.get('response_shape_enforced_category')}")
    if source(packet) != "universal_response_shape":
        failures.append(f"expected universal_response_shape source, got {source(packet)}")
    if call_control(packet) != "continue-call":
        failures.append(f"expected continue-call, got {call_control(packet)}")
    if not final_response(packet).strip():
        failures.append("missing final response")
    if has_any(response, INTERNAL_PATTERNS):
        failures.append("internal wording leaked")
    if has_any(response, UNSAFE_CLAIM_PATTERNS):
        failures.append("unsafe or invented claim leaked")
    if has_any(response, FULL_MENU_PATTERNS):
        failures.append("full diagnostic menu repeated")
    if final_response(packet).count("?") > 1:
        failures.append("response asks more than one question")
    if campaign["generic"] and has_any(response, GENERIC_ROUTE_SIGNAL_LEAKS):
        failures.append("RouteSignal leakage in generic campaign")
    active_side_effects = [name for name, active in side_effect_flags(packet).items() if active]
    if active_side_effects:
        failures.append(f"side effects active: {active_side_effects}")
    return failures


def evaluate_direct(packet: dict[str, Any], campaign: dict[str, Any], expected_move: str) -> list[str]:
    failures = evaluate_common(packet=packet, campaign=campaign, expected_move=expected_move, category="direct_product_value_questions")
    response = lower_response(packet)
    if not any(token in response for token in {"purpose", "helps", "for", "checks", "review", "useful", "mainly", "limited scope", "only if"}):
        failures.append("direct question was not answered plainly")
    return failures


def evaluate_objection(packet: dict[str, Any], campaign: dict[str, Any], expected_move: str) -> list[str]:
    failures = evaluate_common(packet=packet, campaign=campaign, expected_move=expected_move, category="objections")
    response = lower_response(packet)
    if not any(token in response for token in {"understood", "fair", "makes sense", "got it", "no problem"}):
        failures.append("objection was not acknowledged")
    if any(token in response for token in {"wrong", "but you should", "our competitor"}):
        failures.append("argumentative or competitor-bashing wording")
    if expected_move in {"no_clear_need", "too_busy_now", "timing_objection"} and has_any(response, APPOINTMENT_PRESSURE_PATTERNS):
        failures.append("appointment pressure after no-need, busy, or timing objection")
    return failures


def evaluate_time_pressure(packet: dict[str, Any], campaign: dict[str, Any], expected_move: str) -> list[str]:
    failures = evaluate_common(packet=packet, campaign=campaign, expected_move=expected_move, category="permission_time_pressure")
    response = lower_response(packet)
    if not any(token in response for token in {"quick", "short", "minute"}):
        failures.append("time pressure was not acknowledged")
    if len(final_response(packet).split()) > 32:
        failures.append("time-pressure response is too long")
    if has_any(response, APPOINTMENT_PRESSURE_PATTERNS):
        failures.append("appointment ask before pain")
    return failures


def case_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for transcript, expected in DIRECT_QUESTION_CASES:
        rows.append({"category": "direct_product_value_questions", "transcript": transcript, "expected": expected, "context": "after_permission"})
    for transcript, expected in OBJECTION_CASES:
        rows.append({"category": "objections", "transcript": transcript, "expected": expected, "context": "after_permission"})
    for transcript, expected in TIME_PRESSURE_CASES:
        rows.append({"category": "permission_time_pressure", "transcript": transcript, "expected": expected, "context": "after_open"})
    return rows


def run_target_matrix() -> list[dict[str, Any]]:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    index = 0
    evaluators = {
        "direct_product_value_questions": evaluate_direct,
        "objections": evaluate_objection,
        "permission_time_pressure": evaluate_time_pressure,
    }
    for campaign in CAMPAIGNS:
        for case in case_rows():
            index += 1
            packet = run_sequence(campaign, case["transcript"], case["context"], index)
            failures = evaluators[case["category"]](packet, campaign, case["expected"])
            results.append(
                {
                    "campaign": campaign["id"],
                    "category": case["category"],
                    "transcript": case["transcript"],
                    "expected_buyer_move_id": case["expected"],
                    "actual_buyer_move_id": frame(packet).get("buyer_move_id"),
                    "response_shape_enforcement_enabled": frame(packet).get("response_shape_enforcement_enabled"),
                    "response_shape_enforcement_reason": frame(packet).get("response_shape_enforcement_reason"),
                    "source": source(packet),
                    "call_control": call_control(packet),
                    "final_response": final_response(packet),
                    "universal_policy_frame": frame(packet),
                    "side_effect_flags": side_effect_flags(packet),
                    "failures": failures,
                    "passed": not failures,
                }
            )
    return results


def run_safety_preservation() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    insurance = CAMPAIGNS[1]
    automotive = CAMPAIGNS[3]
    routesignal = CAMPAIGNS[0]

    scenarios = [
        ("generic_asr_play_double", insurance, ["__agent_open__", "yeah sure", "play a double be good"], "asr_garbled_or_low_confidence"),
        ("generic_asr_yadav", insurance, ["__agent_open__", "yeah sure", "premium is a problem", "yadav would be good"], "asr_garbled_or_low_confidence"),
        ("clean_automotive_pain", automotive, ["__agent_open__", "yes", "repair timings are usually pretty long"], "pain_confirmed"),
        ("routesignal_callbacks_clear", routesignal, ["__agent_open__", "yeah sure", "callbacks are fine"], "no_pain_clear"),
    ]
    for index, (name, campaign, turns, expected_move) in enumerate(scenarios, start=1):
        state: dict[str, Any] = {}
        packet: dict[str, Any] = {}
        for turn in turns:
            packet = build_turn(turn, state, campaign, f"safety-{index}-{name}")
        failures: list[str] = []
        policy = frame(packet)
        if policy.get("buyer_move_id") != expected_move:
            failures.append(f"expected buyer_move_id {expected_move}, got {policy.get('buyer_move_id')}")
        if "asr" in name and policy.get("enforcement_enabled") is not True:
            failures.append("generic ASR enforcement not preserved")
        if name == "clean_automotive_pain" and policy.get("asr_repair_required"):
            failures.append("clean pain treated as ASR")
        if name == "routesignal_callbacks_clear":
            response = lower_response(packet)
            if "routesignal" not in response and "callback" not in response:
                failures.append("RouteSignal callback clear path not preserved")
            if policy.get("enforcement_enabled") is True:
                failures.append("RouteSignal universal enforcement unexpectedly enabled")
        active_side_effects = [flag for flag, active in side_effect_flags(packet).items() if active]
        if active_side_effects:
            failures.append(f"side effects active: {active_side_effects}")
        checks.append(
            {
                "name": name,
                "expected_buyer_move_id": expected_move,
                "actual_buyer_move_id": policy.get("buyer_move_id"),
                "enforcement_enabled": policy.get("enforcement_enabled"),
                "response_shape_enforcement_enabled": policy.get("response_shape_enforcement_enabled"),
                "call_control": call_control(packet),
                "final_response": final_response(packet),
                "failures": failures,
                "passed": not failures,
            }
        )
    return checks


def summarize(results: list[dict[str, Any]], safety: list[dict[str, Any]]) -> dict[str, Any]:
    by_category: dict[str, dict[str, int]] = defaultdict(lambda: {"passed": 0, "failed": 0})
    for result in results:
        bucket = by_category[result["category"]]
        if result["passed"]:
            bucket["passed"] += 1
        else:
            bucket["failed"] += 1
    failures = [result for result in results if not result["passed"]]
    safety_failures = [result for result in safety if not result["passed"]]
    return {
        "matrix_size": len(results),
        "pass_count": len(results) - len(failures),
        "failure_count": len(failures),
        "by_category": dict(sorted(by_category.items())),
        "failure_examples": failures[:20],
        "safety_preservation_pass_count": len(safety) - len(safety_failures),
        "safety_preservation_failure_count": len(safety_failures),
        "safety_failures": safety_failures,
    }


def write_evidence(result: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    summary = result["summary"]
    report = [
        f"# {CHECKPOINT_ID}",
        "",
        "## Summary",
        f"Status: {result['status']}",
        f"Target matrix size: {summary['matrix_size']}",
        f"Target pass/fail: {summary['pass_count']} / {summary['failure_count']}",
        f"Safety preservation pass/fail: {summary['safety_preservation_pass_count']} / {summary['safety_preservation_failure_count']}",
        "",
        "## Target Results By Category",
    ]
    for category, counts in summary["by_category"].items():
        report.append(f"- {category}: pass={counts['passed']} fail={counts['failed']}")
    report.extend(["", "## Failure Examples"])
    for item in summary["failure_examples"][:12]:
        report.append(
            f"- {item['campaign']} | {item['category']} | {item['transcript']} | "
            f"failures={item['failures']} | response={item['final_response']!r}"
        )
    report.extend(["", "## Safety Failures"])
    for item in summary["safety_failures"]:
        report.append(f"- {item['name']}: {item['failures']}")
    (OUT_DIR / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")


def main() -> int:
    results = run_target_matrix()
    safety = run_safety_preservation()
    summary = summarize(results, safety)
    side_effects: dict[str, bool] = {}
    for result in results:
        for flag, active in result["side_effect_flags"].items():
            side_effects[flag] = bool(side_effects.get(flag) or active)
    status = "pass" if summary["failure_count"] == 0 and summary["safety_preservation_failure_count"] == 0 and not any(side_effects.values()) else "fail"
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": status,
        "summary": summary,
        "results": results,
        "safety_preservation": safety,
        "side_effects": side_effects,
    }
    write_evidence(result)
    print(json.dumps({k: result[k] for k in ["checkpoint_id", "status", "summary", "side_effects"]}, indent=2, sort_keys=True))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
