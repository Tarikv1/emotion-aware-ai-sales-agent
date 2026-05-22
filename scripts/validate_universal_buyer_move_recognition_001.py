"""Validate UniversalConversationPolicyFrame buyer-move recognition.

This phase checks trace labels only. It does not require broad response-shape
enforcement and does not make provider, live TTS, email, calendar, or CRM calls.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import run_live_demo_001_agent_voice_call as demo  # noqa: E402


CHECKPOINT_ID = "UNIVERSAL-BUYER-MOVE-RECOGNITION-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID
EXAMPLES = ROOT / "runtime" / "campaigns" / "examples"

CAMPAIGNS = [
    {"id": "routesignal_live_demo", "config_path": None, "generic": False},
    {"id": "synthetic-insurance-review", "config_path": EXAMPLES / "synthetic-insurance-review.json", "generic": True},
    {"id": "synthetic-b2b-saas-operations", "config_path": EXAMPLES / "synthetic-b2b-saas-operations.json", "generic": True},
    {"id": "synthetic-automotive-service-review", "config_path": EXAMPLES / "synthetic-automotive-service-review.json", "generic": True},
]

CASES = [
    ("objections", "too expensive", {"price_or_budget_objection"}),
    ("objections", "we already have a provider", {"already_has_provider"}),
    ("objections", "I need to ask my manager", {"no_authority_or_needs_approval"}),
    ("objections", "send me proof", {"wants_proof_or_case_study"}),
    ("objections", "we are too busy", {"too_busy_now"}),
    ("identity_trust_privacy", "who are you", {"who_are_you"}),
    ("identity_trust_privacy", "are you a robot", {"are_you_ai_or_robot"}),
    ("identity_trust_privacy", "how did you get my number", {"how_did_you_get_my_number"}),
    ("identity_trust_privacy", "is this recorded", {"is_this_recorded"}),
    ("identity_trust_privacy", "what do you do with my data", {"privacy_data_use_question"}),
    ("identity_trust_privacy", "I don't want to continue", {"permission_to_continue_denied", "stop_request"}),
    ("product_value_scope", "what problem do you solve", {"what_problem_do_you_solve"}),
    ("product_value_scope", "why should I care", {"why_should_i_care"}),
    ("product_value_scope", "what makes you different", {"what_makes_you_different"}),
    ("product_value_scope", "who is this for", {"who_is_this_for"}),
    ("product_value_scope", "is this worth my time", {"is_this_worth_my_time"}),
    ("product_value_scope", "so you cannot give me details", {"scope_limit_question"}),
    ("product_value_scope", "can you guarantee that", {"regulated_claim_question"}),
    ("product_value_scope", "am I covered", {"regulated_claim_question"}),
    ("product_value_scope", "can you promise the result", {"regulated_claim_question"}),
    ("social_conversation_management", "slow down", {"slow_down_or_speak_faster"}),
    ("social_conversation_management", "say that again", {"repeat_last_answer", "repeat_or_rephrase_request"}),
    ("social_conversation_management", "I don't speak English well", {"language_mismatch"}),
    ("social_conversation_management", "that's not how you say my name", {"pronunciation_or_name_correction"}),
    ("social_conversation_management", "haha okay", {"small_talk", "silence_or_backchannel"}),
    ("social_conversation_management", "you're annoying", {"emotional_frustration", "abusive_or_hostile_buyer"}),
    ("asr_and_clean_controls", "play a double be good", {"asr_garbled_or_low_confidence"}),
    ("asr_and_clean_controls", "yadav would be good", {"asr_garbled_or_low_confidence"}),
    ("asr_and_clean_controls", "repair timings are usually pretty long", {"pain_confirmed", "confusion_not_clear"}),
    ("asr_and_clean_controls", "yeah that would be good", {"appointment_interest", "permission_acknowledgement"}),
]


def lower(value: Any) -> str:
    return str(value or "").lower()


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


def frame(packet: dict[str, Any]) -> dict[str, Any]:
    return packet.get("universal_policy_frame") or (packet.get("dialogue_manager") or {}).get("universal_policy_frame") or {}


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


def context_for(transcript: str) -> list[str]:
    if transcript in {"play a double be good", "yadav would be good", "yeah that would be good"}:
        return ["__agent_open__", "yeah sure", "premium is a problem", transcript]
    if transcript == "repair timings are usually pretty long":
        return ["__agent_open__", "yeah sure", transcript]
    return ["__agent_open__", "yeah sure", transcript]


def run_case(campaign: dict[str, Any], category: str, transcript: str, expected: set[str], index: int) -> dict[str, Any]:
    session_id = f"{index:03d}-{campaign['id']}-{slug(transcript)}"[:120]
    state: dict[str, Any] = {}
    packet: dict[str, Any] = {}
    for turn in context_for(transcript):
        packet = build_turn(turn, state, campaign, session_id)
    policy_frame = frame(packet)
    actual = str(policy_frame.get("buyer_move_id") or "")
    failures: list[str] = []
    if actual not in expected:
        failures.append(f"expected one of {sorted(expected)}, got {actual}")
    if not policy_frame.get("recognition_reason"):
        failures.append("missing recognition_reason")
    if policy_frame.get("recognition_confidence") not in {"high", "medium", "low"}:
        failures.append("missing recognition_confidence")
    if not policy_frame.get("buyer_move_category"):
        failures.append("missing buyer_move_category")
    if transcript in {"play a double be good", "yadav would be good"}:
        if campaign["generic"] and policy_frame.get("enforcement_enabled") is not True:
            failures.append("generic ASR garble enforcement not enabled")
        if not campaign["generic"] and policy_frame.get("enforcement_enabled") is not False:
            failures.append("RouteSignal ASR garble enforcement should remain disabled")
    if transcript in {"repair timings are usually pretty long", "yeah that would be good"}:
        if actual == "asr_garbled_or_low_confidence" or policy_frame.get("asr_repair_required"):
            failures.append("clean control was treated as ASR garble")
    active_side_effects = [name for name, active in side_effect_flags(packet).items() if active]
    if active_side_effects:
        failures.append(f"side effects active: {active_side_effects}")
    return {
        "campaign": campaign["id"],
        "category": category,
        "transcript": transcript,
        "expected_buyer_move_ids": sorted(expected),
        "actual_buyer_move_id": actual,
        "recognition_reason": policy_frame.get("recognition_reason"),
        "recognition_confidence": policy_frame.get("recognition_confidence"),
        "buyer_move_category": policy_frame.get("buyer_move_category"),
        "enforcement_enabled": policy_frame.get("enforcement_enabled"),
        "asr_repair_required": policy_frame.get("asr_repair_required"),
        "side_effect_flags": side_effect_flags(packet),
        "failures": failures,
        "passed": not failures,
    }


def slug(text: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in text.lower()).strip("-")


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    by_category: dict[str, dict[str, int]] = defaultdict(lambda: {"passed": 0, "failed": 0})
    failures = []
    for result in results:
        bucket = by_category[result["category"]]
        if result["passed"]:
            bucket["passed"] += 1
        else:
            bucket["failed"] += 1
            failures.append(result)
    top_actuals = Counter(result["actual_buyer_move_id"] for result in failures).most_common(10)
    return {
        "matrix_size": len(results),
        "pass_count": sum(1 for item in results if item["passed"]),
        "failure_count": len(failures),
        "by_category": dict(sorted(by_category.items())),
        "top_failed_actual_labels": [{"buyer_move_id": label, "count": count} for label, count in top_actuals],
        "failure_examples": failures[:20],
    }


def write_evidence(result: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    report = [
        f"# {CHECKPOINT_ID}",
        "",
        "## Summary",
        f"Status: {result['status']}",
        f"Matrix size: {result['summary']['matrix_size']}",
        f"Pass: {result['summary']['pass_count']}",
        f"Fail: {result['summary']['failure_count']}",
        "",
        "## Recognition By Category",
    ]
    for category, counts in result["summary"]["by_category"].items():
        report.append(f"- {category}: pass={counts['passed']} fail={counts['failed']}")
    report.extend(["", "## Top Failed Actual Labels"])
    for item in result["summary"]["top_failed_actual_labels"]:
        report.append(f"- {item['buyer_move_id']}: {item['count']}")
    report.extend(["", "## Failure Examples"])
    for item in result["summary"]["failure_examples"][:12]:
        report.append(
            f"- {item['campaign']} | {item['category']} | {item['transcript']} | "
            f"expected={item['expected_buyer_move_ids']} actual={item['actual_buyer_move_id']} "
            f"failures={item['failures']}"
        )
    (OUT_DIR / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")


def main() -> int:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    index = 0
    for campaign in CAMPAIGNS:
        for category, transcript, expected in CASES:
            index += 1
            results.append(run_case(campaign, category, transcript, expected, index))
    summary = summarize(results)
    side_effects: dict[str, bool] = {}
    for result in results:
        for name, active in result["side_effect_flags"].items():
            side_effects[name] = bool(side_effects.get(name) or active)
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "pass" if summary["failure_count"] == 0 and not any(side_effects.values()) else "fail",
        "summary": summary,
        "results": results,
        "side_effects": side_effects,
        "runtime_final_responses_changed": False,
    }
    write_evidence(result)
    print(json.dumps({k: result[k] for k in ["checkpoint_id", "status", "summary", "side_effects"]}, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
