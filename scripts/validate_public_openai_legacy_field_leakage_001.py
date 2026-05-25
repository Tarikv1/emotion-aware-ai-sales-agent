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


CHECKPOINT_ID = "PUBLIC-OPENAI-LEGACY-FIELD-LEAKAGE-001"
FIXTURE_PATH = ROOT / "runtime" / "campaigns" / "examples" / "public-openai-chatgpt-plans.json"
B2B_CONFIG = ROOT / "runtime" / "campaigns" / "examples" / "synthetic-b2b-saas-operations.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID

BANNED_RE = re.compile(
    r"legacy compatibility field only|primary close is official self-serve plan page|"
    r"enterprise contact-sales route|demo operator for simulation notes|human_followup_owner|"
    r"appointment_target|short legacy compatibility field|official openai sales team for enterprise can do a short",
    re.I,
)
RAW_URL_RE = re.compile(r"https?://|www\.", re.I)
FAKE_SIDE_EFFECT_RE = re.compile(r"\b(i sent|i emailed|i booked|created .*calendar|created .*crm|send it to your email)\b", re.I)
UNSAFE_AFFILIATION_RE = re.compile(
    r"\b(i am calling from openai|i'm calling from openai|authorized by openai|authorized to represent openai|i represent openai)\b",
    re.I,
)

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


def normalize(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def sha12(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


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


def build_turn(transcript: str, *, config_path: Path | None, state: dict[str, Any], session_id: str) -> dict[str, Any]:
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
        campaign_config_path=config_path,
        session_id=session_id,
        session_state=state,
        asr_confidence=0.94,
        generic_live_tts_allowed=False,
    )
    append_turn(state, packet)
    return packet


def openai_turn(utterance: str, session_id: str) -> dict[str, Any]:
    state: dict[str, Any] = {"turns": []}
    return build_turn(utterance, config_path=FIXTURE_PATH, state=state, session_id=session_id)


def route_signal_sequence() -> dict[str, Any]:
    state: dict[str, Any] = {"turns": []}
    packet: dict[str, Any] = {}
    for utterance in ["__agent_open__", "yeah sure", "callbacks are slipping"]:
        packet = build_turn(utterance, config_path=None, state=state, session_id="routesignal-negative-control")
    return packet


def generic_b2b_turn() -> dict[str, Any]:
    state: dict[str, Any] = {"turns": []}
    return build_turn("manual work is the issue", config_path=B2B_CONFIG, state=state, session_id="generic-b2b-negative-control")


def static_fixture_checks(fixture: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    field_visibility = fixture.get("field_visibility")
    if not isinstance(field_visibility, dict):
        failures.append("fixture missing field_visibility map")
        field_visibility = {}
    for key in ("appointment_target", "human_followup_owner"):
        item = field_visibility.get(key) if isinstance(field_visibility, dict) else None
        if not isinstance(item, dict) or item.get("customer_facing") is not False:
            failures.append(f"{key} is not explicitly marked non-customer-facing")
        if not isinstance(item, dict) or str(item.get("purpose") or "").strip() == "":
            failures.append(f"{key} missing internal compatibility purpose")

    next_steps = fixture.get("customer_facing_next_steps")
    if not isinstance(next_steps, dict):
        failures.append("fixture missing customer_facing_next_steps alternatives")
        next_steps = {}
    required_next_steps = [
        "self_serve_close",
        "contact_sales_route",
        "after_interest",
        "enterprise_questions_owner",
        "no_side_effect_reason",
    ]
    for key in required_next_steps:
        if not str(next_steps.get(key) or "").strip():
            failures.append(f"customer_facing_next_steps missing {key}")

    if not fixture.get("self_serve_close_spoken_label"):
        failures.append("self_serve_close_spoken_label missing")
    if not fixture.get("contact_sales_target"):
        failures.append("contact_sales_target missing")
    return failures, {
        "field_visibility": field_visibility,
        "customer_facing_next_step_keys": sorted(next_steps),
    }


def validate_openai_response(case: dict[str, Any]) -> dict[str, Any]:
    packet = openai_turn(case["utterance"], case["id"])
    text = response_text(packet)
    lowered = normalize(text)
    failures: list[str] = []
    for phrase in case.get("must_include", []):
        if phrase.lower() not in lowered:
            failures.append(f"missing required phrase {phrase!r}")
    if case.get("any_include") and not any(phrase.lower() in lowered for phrase in case["any_include"]):
        failures.append(f"missing one of {case['any_include']!r}")
    banned = BANNED_RE.findall(text)
    if banned:
        failures.append(f"banned legacy/internal phrase spoken: {sorted(set(banned))}")
    if RAW_URL_RE.search(text):
        failures.append("raw URL spoken")
    if FAKE_SIDE_EFFECT_RE.search(text):
        failures.append("fake email/calendar/CRM side-effect claim")
    if UNSAFE_AFFILIATION_RE.search(text):
        failures.append("unsafe OpenAI affiliation claim")
    flags = side_effect_flags(packet)
    for key in SIDE_EFFECT_KEYS:
        if flags[key]:
            failures.append(f"{key} must be false")
    if flags["live_tts_used"] or flags["tts_provider_calls_made"] or flags["audio_file_created"]:
        failures.append("validator must not use live TTS or create audio")
    return {
        "id": case["id"],
        "utterance_label": case["utterance_label"],
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "final_response": text,
        "final_response_hash": sha12(text),
        "side_effects": flags,
    }


def validate_negative_controls() -> tuple[list[str], dict[str, Any]]:
    failures: list[str] = []
    route_signal = route_signal_sequence()
    route_text = response_text(route_signal)
    route_norm = normalize(route_text)
    if route_signal.get("campaign_id") != "campaign-prod-005-b2b-software":
        failures.append("RouteSignal default campaign changed")
    if "callback" not in route_norm and "workflow review" not in route_norm and "northstar" not in route_norm:
        failures.append("RouteSignal appointment/callback language was not preserved")

    generic = generic_b2b_turn()
    generic_text = response_text(generic)
    if generic.get("campaign_id") == "public-openai-chatgpt-plans":
        failures.append("generic B2B negative control resolved to OpenAI")
    if "ChatGPT" in generic_text or "OpenAI" in generic_text:
        failures.append("OpenAI facts leaked into generic B2B response")

    return failures, {
        "routesignal": {
            "campaign_id": route_signal.get("campaign_id"),
            "response_hash": sha12(route_text),
            "response_preview": route_text[:220],
        },
        "generic_b2b": {
            "campaign_id": generic.get("campaign_id"),
            "response_hash": sha12(generic_text),
            "response_preview": generic_text[:220],
        },
    }


def write_evidence(result: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = "\n".join(
        [
            f"# {CHECKPOINT_ID}",
            "",
            f"- Status: `{result['status']}`",
            f"- Static fixture failures: `{len(result['static_fixture_failures'])}`",
            f"- Response cases: `{result['response_case_count']}`",
            f"- Failed response cases: `{result['failed_response_case_count']}`",
            f"- Legacy leakage count: `{result['legacy_field_leakage_count']}`",
            f"- Human owner leakage count: `{result['human_followup_owner_leakage_count']}`",
            f"- Side effects false: `{str(result['side_effects_false']).lower()}`",
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
    fixture = campaign_registry.load_campaign_config(FIXTURE_PATH)
    response_cases = [
        {
            "id": "openai-follow-up-after-this",
            "utterance_label": "who follows up after this",
            "utterance": "who follows up after this",
            "group": "followup_route",
            "must_include": ["there is no follow-up needed", "official ChatGPT plans page", "contact sales"],
        },
        {
            "id": "openai-demo-operator",
            "utterance_label": "who is the demo operator",
            "utterance": "who is the demo operator",
            "group": "operator_boundary",
            "must_include": ["internal public-data simulation", "not representing OpenAI", "not booking follow-up"],
        },
        {
            "id": "openai-who-contacts-me",
            "utterance_label": "who contacts me after this",
            "utterance": "who contacts me after this",
            "group": "followup_route",
            "must_include": ["individual plans", "self-serve", "Enterprise", "contact sales"],
        },
        {
            "id": "openai-what-happens-after-yes",
            "utterance_label": "what happens after I say yes",
            "utterance": "what happens after I say yes",
            "group": "after_interest",
            "must_include": ["self-serve", "official ChatGPT plans page", "Enterprise", "contact sales"],
        },
    ]
    traces = [validate_openai_response(case) | {"group": case["group"]} for case in response_cases]
    static_failures, static_evidence = static_fixture_checks(fixture)
    negative_failures, negative_evidence = validate_negative_controls()
    failed = [trace for trace in traces if trace["status"] != "pass"]
    group_counts = Counter(trace["group"] for trace in traces)
    side_effects_false = all(not any(trace["side_effects"].get(key) for key in SIDE_EFFECT_KEYS) for trace in traces)
    provider_calls = any(trace["side_effects"].get("provider_calls_made") or trace["side_effects"].get("tts_provider_calls_made") for trace in traces)
    result = {
        "status": "pass" if not static_failures and not negative_failures and not failed else "fail",
        "checkpoint_id": CHECKPOINT_ID,
        "static_fixture_failures": static_failures,
        "static_fixture_evidence": static_evidence,
        "negative_control_failures": negative_failures,
        "negative_control_evidence": negative_evidence,
        "response_case_count": len(traces),
        "failed_response_case_count": len(failed),
        "group_counts": dict(sorted(group_counts.items())),
        "legacy_field_leakage_count": sum(1 for trace in traces if BANNED_RE.search(trace["final_response"])),
        "human_followup_owner_leakage_count": sum(1 for trace in traces if re.search(r"human_followup_owner|demo operator", trace["final_response"], re.I)),
        "raw_URL_spoken_count": sum(1 for trace in traces if RAW_URL_RE.search(trace["final_response"])),
        "fake_side_effect_claim_count": sum(1 for trace in traces if FAKE_SIDE_EFFECT_RE.search(trace["final_response"])),
        "unsafe_affiliation_claim_count": sum(1 for trace in traces if UNSAFE_AFFILIATION_RE.search(trace["final_response"])),
        "side_effects_false": side_effects_false,
        "provider_calls_made": provider_calls,
        "live_tts_calls_made": False,
        "local_llm_calls_made": False,
        "raw_private_transcript_copied_to_public_evidence": False,
        "traces": traces,
    }
    write_evidence(result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "failed_response_case_count": result["failed_response_case_count"],
                "static_fixture_failures": len(static_failures),
                "negative_control_failures": len(negative_failures),
            },
            indent=2,
            sort_keys=True,
        )
    )
    if result["status"] != "pass":
        sys.exit(1)


if __name__ == "__main__":
    main()
