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

from runtime.core import campaign_registry  # noqa: E402
import scripts.run_live_demo_001_agent_voice_call as demo  # noqa: E402


CHECKPOINT_ID = "PUBLIC-OPENAI-FRESH-LIVE-REPLAY-001"
FIXTURE_PATH = ROOT / "runtime" / "campaigns" / "examples" / "public-openai-chatgpt-plans.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID

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

LEGACY_RE = re.compile(r"legacy compatibility|appointment_target|RouteSignal|NorthStar|workflow review", re.I)
OWNER_RE = re.compile(r"human_followup_owner|demo operator", re.I)
RAW_URL_RE = re.compile(r"https?://|www\.", re.I)
FAKE_SIDE_EFFECT_RE = re.compile(r"\b(i sent|i emailed|i booked|created .*calendar|created .*crm|send it to your email)\b", re.I)
UNSAFE_AFFILIATION_RE = re.compile(
    r"\b(i am calling from openai|i'm calling from openai|authorized by openai|authorized to represent openai|i represent openai)\b",
    re.I,
)


def normalize(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def scenario(
    scenario_id: str,
    group: str,
    turns: list[str],
    *,
    must_include: list[str] | None = None,
    any_include: list[str] | None = None,
    forbid: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": scenario_id,
        "group": group,
        "turns": turns,
        "must_include": must_include or [],
        "any_include": any_include or [],
        "forbid": forbid or [],
    }


def build_scenarios() -> list[dict[str, Any]]:
    return [
        scenario(
            "fresh-001-opening-disclaimer",
            "affiliation_disclaimer",
            ["__agent_open__"],
            must_include=["public-data", "simulation"],
            forbid=["I am calling from OpenAI", "authorized by OpenAI", "legacy compatibility"],
        ),
        scenario(
            "fresh-002-plan-categories",
            "source_grounded_plan_categories",
            ["__agent_open__", "yes", "what plans are available"],
            must_include=["Free, Go, Plus, Pro, Business, and Enterprise"],
            forbid=["GPT-5.5", "superior", "better than"],
        ),
        scenario(
            "fresh-003-self-serve-close",
            "self_serve_close",
            [
                "__agent_open__",
                "yes",
                "I already use ChatGPT",
                "I use it for coding and writing",
                "I use it heavily every day",
                "I want Plus",
                "sounds good, how do I sign up",
            ],
            must_include=["official ChatGPT plans page"],
            forbid=["http", "sent", "emailed", "booked", "calendar", "CRM"],
        ),
        scenario(
            "fresh-004-email-side-effect",
            "side_effect_boundary",
            ["send me the link by email"],
            any_include=["cannot send email", "can't send email", "can point you"],
            forbid=["I sent", "I emailed", "created a CRM"],
        ),
        scenario(
            "fresh-005-affiliation-question",
            "affiliation_disclaimer",
            ["are you calling from OpenAI?"],
            must_include=["simulation"],
            forbid=["I am calling from OpenAI", "authorized by OpenAI", "I represent OpenAI"],
        ),
        scenario(
            "fresh-006-api-boundary",
            "source_grounded_api_boundary",
            ["is API usage included with Plus?"],
            must_include=["API usage is separate"],
            forbid=["included with Plus", "guarantee"],
        ),
        scenario(
            "fresh-007-current-defect-follow-up-purpose",
            "fresh_live_defect_replay",
            ["who follows up after this"],
            any_include=["plan fit", "official", "ChatGPT"],
            forbid=["legacy compatibility", "appointment_target", "human_followup_owner", "demo operator"],
        ),
        scenario(
            "fresh-008-current-defect-operator-question",
            "fresh_live_defect_replay",
            ["who is the demo operator"],
            any_include=["simulation", "plan fit", "official"],
            forbid=["legacy compatibility", "appointment_target", "human_followup_owner", "demo operator"],
        ),
    ]


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
    summary = packet.get("summary") or {}
    body = packet.get("packet") or {}
    manager = packet.get("dialogue_manager") or {}
    return str(summary.get("final_response") or body.get("final_response") or manager.get("final_response") or "")


def side_effect_flags(packet: dict[str, Any]) -> dict[str, bool]:
    body = packet.get("packet") or {}
    delivery = body.get("tts_delivery") or {}
    summary = packet.get("summary") or {}
    return {
        "provider_calls_made": bool(packet.get("provider_calls_made") or delivery.get("provider_calls_made")),
        "local_llm_calls_made": bool(packet.get("local_llm_calls_made")),
        "sends_email": bool(packet.get("sends_email")),
        "creates_calendar_event": bool(packet.get("creates_calendar_event")),
        "writes_crm": bool(packet.get("writes_crm")),
        "opens_prod_102": bool(packet.get("opens_prod_102")),
        "customer_audio_uploaded_to_python_server": bool(packet.get("customer_audio_uploaded_to_python_server")),
        "customer_audio_uploaded_to_tts_provider": bool(packet.get("customer_audio_uploaded_to_tts_provider") or delivery.get("customer_audio_uploaded")),
        "live_tts_used": bool(packet.get("live_tts_used") or summary.get("live_tts_used")),
        "tts_provider_calls_made": bool(packet.get("tts_provider_calls_made") or summary.get("tts_provider_calls_made")),
        "audio_file_created": bool(packet.get("audio_file_created") or summary.get("tts_audio_file_created")),
    }


def validate_trace(item: dict[str, Any], packet: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    text = response_text(packet)
    lowered = normalize(text)
    for phrase in item["must_include"]:
        if phrase.lower() not in lowered:
            failures.append(f"missing required phrase {phrase!r}")
    if item["any_include"] and not any(phrase.lower() in lowered for phrase in item["any_include"]):
        failures.append(f"missing one of {item['any_include']!r}")
    for phrase in item["forbid"]:
        if phrase.lower() in lowered:
            failures.append(f"forbidden phrase {phrase!r}")
    if LEGACY_RE.search(text):
        failures.append("legacy compatibility leakage")
    if OWNER_RE.search(text):
        failures.append("human_followup_owner leakage")
    if RAW_URL_RE.search(text):
        failures.append("raw URL spoken")
    if FAKE_SIDE_EFFECT_RE.search(text):
        failures.append("fake email/calendar/CRM side-effect claim")
    if UNSAFE_AFFILIATION_RE.search(text):
        failures.append("unsafe affiliation or authorization claim")
    flags = side_effect_flags(packet)
    for key in SIDE_EFFECT_KEYS:
        if flags[key]:
            failures.append(f"{key} must be false")
    if flags["live_tts_used"] or flags["tts_provider_calls_made"] or flags["audio_file_created"]:
        failures.append("validator must stay dry-run with no provider TTS/audio")
    if item["group"] == "self_serve_close":
        selected = packet.get("selected_campaign_config") or {}
        if selected.get("close_mode") != "self_serve_purchase_link":
            failures.append("self-serve close mode missing")
        if selected.get("self_serve_close_spoken_label") != "the official ChatGPT plans page":
            failures.append("voice-ready spoken close label missing")
        if selected.get("should_speak_raw_url") is not False:
            failures.append("raw URL policy must remain false")
        if selected.get("link_available_in_packet") is not True:
            failures.append("operator packet link availability must remain true")
        if selected.get("can_send_email") is not False:
            failures.append("email sending capability must remain false")
    return failures


def run_scenario(item: dict[str, Any]) -> dict[str, Any]:
    state: dict[str, Any] = {"turns": []}
    packet: dict[str, Any] = {}
    for turn in item["turns"]:
        packet = build_turn(turn, state, item["id"])
    text = response_text(packet)
    failures = validate_trace(item, packet)
    selected = packet.get("selected_campaign_config") or {}
    return {
        "id": item["id"],
        "group": item["group"],
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "final_response": text,
        "final_response_hash": hashlib.sha256(text.encode("utf-8")).hexdigest()[:12],
        "close_mode": selected.get("close_mode"),
        "call_control": (packet.get("dialogue_manager") or {}).get("call_control"),
        "side_effects": side_effect_flags(packet),
    }


def fixture_source_fact_result() -> dict[str, Any]:
    fixture = campaign_registry.load_campaign_config(FIXTURE_PATH)
    allowed = set(fixture.get("allowed_claim_fact_ids") or [])
    grounded = fixture.get("source_grounded_claims") or []
    grounded_ids = {str(item.get("fact_id")) for item in grounded if isinstance(item, dict) and item.get("fact_id")}
    required = {
        "pricing_plan_set_001",
        "plus_api_separate_001",
        "business_api_separate_001",
        "enterprise_api_membership_separate_001",
    }
    missing = sorted(required - allowed - grounded_ids)
    return {
        "source_grounded_claim_ids_present": not missing and bool(allowed) and bool(grounded_ids),
        "required_fact_ids_checked": sorted(required),
        "missing_required_fact_ids": missing,
        "allowed_claim_fact_id_count": len(allowed),
        "source_grounded_claim_count": len(grounded_ids),
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
            f"- Failed count: `{result['failed_count']}`",
            f"- Legacy leakage count: `{result['legacy_compatibility_leakage_count']}`",
            f"- Human owner leakage count: `{result['human_followup_owner_leakage_count']}`",
            f"- Raw URL spoken count: `{result['raw_URL_spoken_count']}`",
            f"- Fake side-effect claim count: `{result['fake_side_effect_claim_count']}`",
            f"- Source-grounded claim IDs present: `{str(result['source_grounded_claim_ids_present']).lower()}`",
            f"- Provider calls made: `{str(result['provider_calls_made']).lower()}`",
            "",
            "## Group Counts",
            "",
            "```json",
            json.dumps(result["group_counts"], indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> None:
    scenarios = build_scenarios()
    traces = [run_scenario(item) for item in scenarios]
    failures = [trace for trace in traces if trace["status"] != "pass"]
    group_counts = Counter(trace["group"] for trace in traces)
    source_fact = fixture_source_fact_result()
    provider_calls = any(trace["side_effects"].get("provider_calls_made") or trace["side_effects"].get("tts_provider_calls_made") for trace in traces)
    result = {
        "status": "pass" if not failures and source_fact["source_grounded_claim_ids_present"] else "fail",
        "checkpoint_id": CHECKPOINT_ID,
        "scenario_count": len(scenarios),
        "failed_count": len(failures),
        "group_counts": dict(sorted(group_counts.items())),
        "legacy_compatibility_leakage_count": sum(1 for trace in traces if LEGACY_RE.search(trace["final_response"])),
        "human_followup_owner_leakage_count": sum(1 for trace in traces if OWNER_RE.search(trace["final_response"])),
        "raw_URL_spoken_count": sum(1 for trace in traces if RAW_URL_RE.search(trace["final_response"])),
        "fake_side_effect_claim_count": sum(1 for trace in traces if FAKE_SIDE_EFFECT_RE.search(trace["final_response"])),
        "affiliation_disclaimer_safe": not any(UNSAFE_AFFILIATION_RE.search(trace["final_response"]) for trace in traces),
        "self_serve_close_voice_ready": not any(trace["group"] == "self_serve_close" and trace["status"] != "pass" for trace in traces),
        "side_effects_false": all(not any(trace["side_effects"].get(key) for key in SIDE_EFFECT_KEYS) for trace in traces),
        "provider_calls_made": provider_calls,
        "live_tts_calls_made": False,
        "raw_private_transcript_copied_to_public_evidence": False,
        **source_fact,
        "traces": traces,
    }
    write_evidence(result)
    print(json.dumps({"status": result["status"], "scenario_count": len(scenarios), "failed_count": len(failures)}, indent=2, sort_keys=True))
    if result["status"] != "pass":
        sys.exit(1)


if __name__ == "__main__":
    main()
