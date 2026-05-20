#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import mimetypes
import os
import re
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core.realtime_turns import load_realtime_cases  # noqa: E402
from runtime.contracts.voice_turn_state_contract import (  # noqa: E402
    RESTART_AFTER_AGENT_OUTPUT_MS,
    turn_taking_packet,
    voice_turn_state_metadata,
)
from runtime.core.dialogue_reasoner import (  # noqa: E402
    build_reasoning_context,
    reason_about_turn,
    validate_reasoning_packet,
)
from runtime.core.dialogue_reasoner_async_enrichment import build_async_enrichment_request  # noqa: E402
import runtime.core.live_voice_session_policy as session_policy  # noqa: E402
from runtime.entrypoints.generate_guarded_response import (  # noqa: E402
    DEFAULT_RETRIEVAL_REGISTRY,
    build_guarded_response_packet,
)
from runtime.entrypoints.realtime_turn_cli import find_campaign  # noqa: E402
from runtime.speech.asr_quality_gate import (  # noqa: E402
    ASR_LOW_CONFIDENCE_THRESHOLD,
    evaluate_asr_quality,
    repair_response_for_quality_gate,
)
from runtime.speech.realtime_turn_taking_policy import (  # noqa: E402
    browser_asr_acceptance_policy,
    realtime_turn_taking_policy,
)
from runtime.providers.tts_provider_clients import resolve_voice_id  # noqa: E402
from runtime.voice.runtime_tts_delivery import attach_runtime_tts_delivery, provider_for_key  # noqa: E402
from runtime.voice.runtime_voice_delivery import attach_runtime_voice_delivery  # noqa: E402


DEFAULT_CASES_PATH = ROOT / "research" / "experiments" / "cases" / "prod-005-realtime-latency-call-control.json"
DEFAULT_LIVE_DEMO_PROFILE_PATH = ROOT / "research" / "experiments" / "cases" / "live-demo-001-fictional-b2b-sales-campaign.json"
DEFAULT_CAMPAIGN_ID = "campaign-prod-005-b2b-software"
DEFAULT_STAGE = "relevance-check"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8781
DEFAULT_PRIVATE_OUT = ROOT / "data" / "private" / "live-demo-001"
DEFAULT_ELEVENLABS_ENV_FILE = ROOT / "runtime" / "config" / "local" / "elevenlabs.env"
LIVE_DEMO_ID = "LIVE-DEMO-001"
SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|sk_[A-Za-z0-9_-]{20,}|ELEVENLABS_API_KEY\s*=\s*[^\s]+|xi-api-key\s*[:=]\s*[A-Za-z0-9]|Authorization:\s*Bearer\s+[A-Za-z0-9])"
)
LIVE_TTS_ENV_KEYS = {
    "ELEVENLABS_API_KEY",
    "ELEVENLABS_VOICE_ID",
    "ELEVENLABS_VOICE_ID_EN",
    "ELEVENLABS_VOICE_ID_DE",
}
LIVE_DEMO_B2B_FACT_OVERLAY = {
    "pricing_summary": "Starter is $29/month. Growth is $59/month.",
    "guided_option_plan_29_features": "lead capture and basic routing",
    "guided_option_plan_59_added_features": "priority routing, reminders, duplicate checks, Slack alerts, and handoff review",
    "guided_option_customer_goal": "reduce missed follow-up and manual lead handoff work",
    "guided_option_customer_pain": "shared-inbox leads, wrong-owner routing, missed callbacks, or slow handoffs",
}


def resolve_project_path(path_text: str | None) -> Path | None:
    if path_text is None:
        return None
    path = Path(path_text)
    return path if path.is_absolute() else ROOT / path


def project_relative_string(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if SECRET_PATTERN.search(serialized):
        raise SystemExit("Refusing to write LIVE-DEMO-001 output because a secret-like token appeared.")
    path.write_text(serialized, encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if SECRET_PATTERN.search(text):
        raise SystemExit("Refusing to write LIVE-DEMO-001 text because a secret-like token appeared.")
    path.write_text(text, encoding="utf-8")


def load_live_tts_env_file(path: Path | None) -> dict:
    if path is None or not path.exists():
        return {
            "path": project_relative_string(path),
            "present": False,
            "loaded_keys": [],
            "ignored_keys": [],
        }
    loaded_keys: list[str] = []
    ignored_keys: list[str] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key not in LIVE_TTS_ENV_KEYS:
            ignored_keys.append(key)
            continue
        if value and not os.environ.get(key):
            os.environ[key] = value
            loaded_keys.append(key)
    return {
        "path": project_relative_string(path),
        "present": True,
        "loaded_keys": sorted(loaded_keys),
        "ignored_keys": sorted(ignored_keys),
    }


def live_tts_preflight(campaign_id: str, cases_path: Path, force_key_missing: bool) -> dict:
    provider = provider_for_key("elevenlabs")
    campaign = load_campaign(campaign_id, cases_path)
    language = str(campaign.get("language") or "en")
    api_key_present = False if force_key_missing else bool(os.environ.get(provider["api_key_env_var"]))
    voice_id, voice_source = resolve_voice_id(provider, language, force_key_missing)
    return {
        "provider": "elevenlabs",
        "language": language,
        "api_key_env_var": provider["api_key_env_var"],
        "api_key_present": api_key_present,
        "voice_id_present": bool(voice_id),
        "voice_id_source": voice_source,
    }


def require_live_tts_ready(preflight: dict, env_file_status: dict) -> None:
    missing = []
    if not preflight["api_key_present"]:
        missing.append(preflight["api_key_env_var"])
    if not preflight["voice_id_present"]:
        missing.append("ElevenLabs voice ID")
    if not missing:
        return
    env_path = env_file_status.get("path") or project_relative_string(DEFAULT_ELEVENLABS_ENV_FILE)
    raise SystemExit(
        "LIVE-DEMO-001 was started with --live-tts, but ElevenLabs is not ready. "
        f"Missing: {', '.join(missing)}. "
        f"Set ELEVENLABS_API_KEY in the current shell or in {env_path}; "
        "keep the voice ID in ELEVENLABS_VOICE_ID_EN, ELEVENLABS_VOICE_ID, "
        "runtime/config/local/voice_ids.json, or config/local/voice_ids.json."
    )


def load_live_demo_profile(path: Path = DEFAULT_LIVE_DEMO_PROFILE_PATH) -> dict:
    profile = json.loads(path.read_text(encoding="utf-8"))
    if profile.get("applies_to_campaign_id") != DEFAULT_CAMPAIGN_ID:
        raise SystemExit(f"LIVE-DEMO-001 profile does not apply to {DEFAULT_CAMPAIGN_ID}.")
    return profile


def apply_live_demo_profile(campaign: dict) -> dict:
    profile = load_live_demo_profile()
    company = profile["fictional_company"]
    knowledge = profile["product_knowledge"]
    response_policy = profile["response_policy"]
    sales_delivery_guidance = profile.get("sales_delivery_guidance", {})
    plans = {plan["plan_id"]: plan for plan in knowledge["plans"]}
    emphasis_priority = list(sales_delivery_guidance.get("emphasis_priority") or [])
    campaign.update(LIVE_DEMO_B2B_FACT_OVERLAY)
    campaign.update(
        {
            "client_name": company["client_name"],
            "product_name": company["product_name"],
            "product_category": company["product_category"],
            "approved_opening": "Hi, I am calling about RouteSignal CRM and inbound lead handoff gaps. Do you have a minute?",
            "qualification_questions": [
                "How are inbound demo requests routed today?",
                "Where does follow-up break first: owner assignment, reminders, or handoff review?",
                "Would a short workflow review be useful if those gaps are real?",
            ],
            "allowed_claims": [
                company["one_sentence_positioning"],
                knowledge["short_product_explanation"],
                knowledge["integration_boundary"]["safe_summary"],
                "The first workflow review is informational and does not collect payment.",
            ],
            "forbidden_claims": response_policy["forbidden_claims"],
            "required_disclosures": [
                "This is a fictional local demo campaign, not a real client quote.",
                knowledge["integration_boundary"]["exact_setup_boundary"],
                "Security questions require verified security material before a rollout claim.",
            ],
            "escalation_triggers": response_policy["handoff_only_for"],
            "scheduling_goal": "non-binding workflow review",
            "human_handoff_role": "verified implementation reviewer",
            "caller_identity": profile.get("caller_identity", {}),
            "target_account_context": profile.get("target_account_context", {}),
            "sales_delivery_guidance": sales_delivery_guidance,
            "sales_emphasis_priority": emphasis_priority,
            "voice_listening_calibration": {
                "allowed_emphasis_targets": {
                    "en": emphasis_priority,
                }
            },
            "product_knowledge": knowledge,
            "ideal_customer_profile": profile["ideal_customer_profile"],
            "source_inspiration": profile["source_inspiration"],
            "reuse_boundary": profile["source_policy"],
            "live_demo_fictional_profile_applied": True,
            "live_demo_profile_path": project_relative_string(DEFAULT_LIVE_DEMO_PROFILE_PATH),
            "guided_option_plan_29_features": ", ".join(plans["starter"]["included"][:2]),
            "guided_option_plan_59_added_features": ", ".join(plans["growth"]["included"][:5]),
        }
    )
    return campaign


def elapsed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 3)


def load_campaign(campaign_id: str, cases_path: Path) -> dict:
    campaigns, _cases = load_realtime_cases(cases_path)
    campaign = dict(find_campaign(campaigns, campaign_id))
    if campaign_id == DEFAULT_CAMPAIGN_ID:
        campaign = apply_live_demo_profile(campaign)
        campaign["live_demo_fact_overlay_applied"] = True
    return campaign


def campaign_options(cases_path: Path) -> list[dict]:
    campaigns, _cases = load_realtime_cases(cases_path)
    options = []
    for campaign in campaigns:
        option_campaign = dict(campaign)
        if option_campaign.get("campaign_id") == DEFAULT_CAMPAIGN_ID:
            option_campaign = apply_live_demo_profile(option_campaign)
        options.append(
            {
                "campaign_id": option_campaign.get("campaign_id"),
                "language": option_campaign.get("language"),
                "product_name": option_campaign.get("product_name"),
                "client_name": option_campaign.get("client_name"),
            }
        )
    return options


def build_metadata(args: argparse.Namespace, cases_path: Path, private_out: Path) -> dict:
    profile = load_live_demo_profile()
    return {
        "live_demo_id": LIVE_DEMO_ID,
        "purpose": "Talk to the repo-owned sales agent through browser ASR and ElevenLabs voice output.",
        "local_server": {
            "host": args.host,
            "port": args.port,
            "url": f"http://{args.host}:{args.port}/",
            "endpoints": ["/", "/metadata", "/turn", "/audio"],
        },
        "default_campaign_id": args.campaign,
        "default_stage": args.stage,
        "campaign_options": campaign_options(cases_path),
        "case_file": project_relative_string(cases_path),
        "fictional_campaign_profile": {
            "profile_id": profile["profile_id"],
            "profile_path": project_relative_string(DEFAULT_LIVE_DEMO_PROFILE_PATH),
            "client_name": profile["fictional_company"]["client_name"],
            "product_name": profile["fictional_company"]["product_name"],
            "source_policy": profile["source_policy"],
            "source_urls": [source["url"] for source in profile["source_inspiration"]],
        },
        "private_output_dir": project_relative_string(private_out),
        "browser_asr": {
            "enabled": True,
            "provider": "browser SpeechRecognition or webkitSpeechRecognition",
            "audio_sent_to_python_server": False,
            "browser_vendor_may_process_audio": True,
            "consent_required_in_ui": True,
            "supported_languages": ["en-US", "de-DE", "tr-TR"],
            "acceptance_policy": browser_asr_acceptance_policy(),
            "turn_taking_policy": realtime_turn_taking_policy(),
        },
        "turn_taking": voice_turn_state_metadata(),
        "repo_owned_agent": {
            "brain_source": "runtime.entrypoints.generate_guarded_response + runtime.voice runtime delivery",
            "llm_used": False,
            "provider_agent_used": False,
            "durable_provider_agent_created": False,
            "demo_session_continuity": True,
            "guarded_retrieval": {
                "enabled_when_registry_present": DEFAULT_RETRIEVAL_REGISTRY.exists(),
                "registry_path": project_relative_string(DEFAULT_RETRIEVAL_REGISTRY),
                "scope": "local advisory retrieval for demo turns only; protected contexts still block it",
                "campaign_facts_override_rag": True,
            },
            "composer_hooks": {
                "enabled_when_retrieval_enabled": DEFAULT_RETRIEVAL_REGISTRY.exists(),
                "scope": "candidate response wording only; no decision labels or protected text changes",
            },
        },
        "tts": {
            "provider": "elevenlabs",
            "live_tts_enabled": args.live_tts,
            "force_key_missing": args.force_key_missing,
            "api_key_env_var": "ELEVENLABS_API_KEY",
            "api_key_present_at_start": bool(getattr(args, "live_tts_preflight", {}).get("api_key_present", False)),
            "elevenlabs_env_file": getattr(args, "live_tts_env_file_status", {}),
            "voice_id_sources": [
                "ELEVENLABS_VOICE_ID_EN",
                "ELEVENLABS_VOICE_ID",
                "runtime/config/local/voice_ids.json",
                "config/local/voice_ids.json",
            ],
            "voice_id_present_at_start": bool(getattr(args, "live_tts_preflight", {}).get("voice_id_present", False)),
            "selected_voice_id_source_at_start": getattr(args, "live_tts_preflight", {}).get("voice_id_source"),
            "customer_audio_uploaded_to_tts_provider": False,
            "text_sent_to_tts_provider_when_live": True,
            "voice_cloning_used": False,
            "timeout_seconds": args.timeout_seconds,
        },
        "playback": {
            "agent_audio_volume": 0.68,
            "browser_fallback_voice_volume": 0.68,
            "browser_fallback_voice_rate": 1.01,
            "manual_interrupt_enabled": True,
            "manual_interrupt_shortcut": "Escape",
            "spoken_barge_in_enabled": False,
            "spoken_barge_in_blocked_reason": "Browser SpeechRecognition cannot safely separate the buyer from the agent audio in this demo.",
            "transcript_panel_enabled": True,
            "transcript_download_enabled": True,
            "transcript_stores_audio_data": False,
            "transcript_scope": "browser session text only; private turn packets remain under ignored local output",
            "volume_applied_in_browser_only": True,
            "provider_audio_file_unchanged": True,
        },
        "boundaries": {
            "real_customer_audio_allowed": False,
            "tarik_mic_demo_allowed": args.consent_confirmed,
            "runtime_behavior_changed": False,
            "opens_prod_102": False,
            "stores_turns_under_ignored_private_data": True,
        },
    }


def decision_summary(packet: dict) -> dict:
    decision = packet["decision_snapshot"]
    tts = packet["tts_delivery"]
    retrieval = packet.get("retrieval", {})
    composer_hooks = packet.get("composer_hooks", {})
    return {
        "sales_difficulty": decision.get("sales_difficulty"),
        "detected_emotion": decision.get("detected_emotion"),
        "interest_state": decision.get("interest_state"),
        "selected_strategy": decision.get("selected_strategy"),
        "next_action": decision.get("next_action"),
        "call_control": decision.get("call_control"),
        "final_response": packet["final_response"],
        "tts_input_source": tts["tts_input_source"],
        "tts_input_text": tts["tts_input_text"],
        "browser_fallback_speech_text": browser_fallback_speech_text(tts["tts_input_text"]),
        "tts_provider_rendering_used": tts["provider_rendering_used"],
        "retrieval_status": retrieval.get("status"),
        "retrieval_used_in_runtime": retrieval.get("retrieval_used_in_runtime"),
        "retrieved_item_ids": retrieval.get("retrieved_item_ids", []),
        "composer_hooks_status": composer_hooks.get("status"),
        "composer_hooks_applied": composer_hooks.get("applied"),
        "tts_provider_calls_made": tts["provider_calls_made"],
        "tts_audio_file_created": tts["audio_file_created"],
        "tts_fallback_reason": tts["fallback_reason"],
        "time_to_first_audio_ms": tts["time_to_first_audio_ms"],
        "total_provider_latency_ms": tts["total_provider_latency_ms"],
    }


def apply_live_session_decision_overrides(packet: dict, continuity: dict) -> dict:
    if continuity.get("reason") == "buyer_requested_stop":
        decision = packet.get("decision_snapshot", {})
        decision.update(
            {
                "sales_difficulty": "do-not-call",
                "detected_emotion": "skeptical-or-negative",
                "interest_state": "do-not-call",
                "selected_strategy": "rapport",
                "next_action": "suppress-contact",
                "call_control": "end-call",
            }
        )
        packet["decision_snapshot"] = decision
        return packet
    if continuity.get("reason") not in {"callback_time_confirmed", "appointment_time_confirmed"}:
        return packet
    decision = packet.get("decision_snapshot", {})
    sales_difficulty = "appointment-scheduling-confirmation" if continuity.get("reason") == "appointment_time_confirmed" else "scheduling-confirmation"
    next_action = "confirm-appointment" if continuity.get("reason") == "appointment_time_confirmed" else "confirm-scheduling"
    decision.update(
        {
            "sales_difficulty": sales_difficulty,
            "detected_emotion": "positive",
            "interest_state": "interested",
            "selected_strategy": "direct-ask-or-commitment",
            "next_action": next_action,
            "call_control": "schedule-and-end",
        }
    )
    packet["decision_snapshot"] = decision
    return packet


def audio_url_for_packet(packet: dict) -> str | None:
    output = packet["tts_delivery"].get("audio_output_path")
    if not output:
        return None
    return "/audio?path=" + output.replace("\\", "/")


def browser_fallback_speech_text(text: str) -> str:
    stripped = re.sub(r"<[^>]+>", " ", text)
    stripped = re.sub(r"\s+([,.;:!?])", r"\1", stripped)
    stripped = re.sub(r"([,.;:!?])([^\s])", r"\1 \2", stripped)
    return re.sub(r"\s+", " ", stripped).strip()


def normalize_text(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def normalized_contains_any(normalized: str, phrases: set[str]) -> bool:
    return any(normalize_text(phrase) in normalized for phrase in phrases)


def live_demo_price_answer(language: str) -> str:
    if language.startswith("de"):
        return "Der Demo-Preis liegt bei 29 Dollar pro Monat oder 59 Dollar pro Monat, je nach Umfang."
    return "Starter is $29/month for basic routing. Growth is $59/month with priority routing, reminders, and handoff review. Which gap costs more time today: routing, callbacks, or handoffs?"


def is_live_demo_price_answer(response: str) -> bool:
    return "$29/month" in response and "$59/month" in response


def asr_fragment_response(language: str) -> str:
    if language.startswith("de"):
        return "Ich habe nur einen Teil verstanden. Bitte wiederholen Sie die Frage in einem Satz."
    return "I only caught part of that. Please repeat the question in one sentence."


def asr_low_confidence_response(language: str) -> str:
    if language.startswith("de"):
        return "Ich bin mir bei der Spracherkennung nicht sicher. Bitte wiederholen Sie die Frage kurz."
    return "I am not confident I caught that correctly. Please repeat the question briefly."


def asr_quality_gate(transcript: str, asr_confidence: float | None) -> dict:
    normalized = normalize_text(transcript)
    if not normalized:
        return {
            "accepted": False,
            "reason": "empty_transcript",
            "low_confidence_threshold": ASR_LOW_CONFIDENCE_THRESHOLD,
            "confidence": asr_confidence,
        }
    if asr_confidence is not None and asr_confidence < ASR_LOW_CONFIDENCE_THRESHOLD:
        return {
            "accepted": False,
            "reason": "low_confidence",
            "low_confidence_threshold": ASR_LOW_CONFIDENCE_THRESHOLD,
            "confidence": asr_confidence,
        }
    return {
        "accepted": True,
        "reason": "accepted",
        "low_confidence_threshold": ASR_LOW_CONFIDENCE_THRESHOLD,
        "confidence": asr_confidence,
    }


def looks_like_asr_fragment(normalized: str, selected_focus: str | None) -> bool:
    if selected_focus:
        return False
    words = normalized.split()
    if not words:
        return True
    fragment_endings = {"a", "an", "the", "about", "of", "to", "for", "with", "and", "or", "but"}
    return len(words) <= 5 and words[-1] in fragment_endings


def is_opening_greeting(normalized: str) -> bool:
    return normalized in {"hi", "hello", "hey", "hey what s up", "hey whats up", "hi how are you", "how are you"}


def opening_greeting_response(language: str) -> str:
    if language.startswith("de"):
        return "Hallo. Ich kann Preis, Passung oder Workflow-Details klaeren. Womit sollen wir anfangen?"
    return "Hi. I can help with price, fit, or workflow details. What do you want to check first?"


def english_live_demo_campaign_response(normalized: str, campaign: dict) -> dict | None:
    knowledge = campaign.get("product_knowledge") or {}
    if not knowledge or str(campaign.get("language") or "en").lower().startswith("de"):
        return None

    def candidate(reason: str, dialogue_focus: str, response: str) -> dict:
        return {
            "applied": True,
            "reason": reason,
            "dialogue_focus": dialogue_focus,
            "candidate_response": response,
        }

    if normalized_contains_any(normalized, {"soc 2", "soc2", "security", "secure", "compliance"}):
        return candidate(
            "campaign_depth_security_boundary_answered",
            "security",
            "I cannot claim that here. Use verified security material before any serious rollout discussion.",
        )
    if normalized_contains_any(normalized, {"salesforce", "hubspot", "integrate", "integration", "connect with", "crm"}):
        return candidate(
            "campaign_depth_integration_boundary_answered",
            "details",
            "The fictional profile supports owner lookup, but exact setup and permissions need verified review before I claim fit.",
        )
    if normalized_contains_any(normalized, {"do i need to talk to a specialist", "need a specialist", "talk to a specialist"}):
        return candidate(
            "campaign_depth_unnecessary_handoff_answered",
            "details",
            "Not for basics. I can cover price, fit, and workflow here. Exact security or integration proof needs verified review.",
        )
    if normalized_contains_any(normalized, {"fifty nine", "59 dollars", "$59", "growth plan", "growth"}) and normalized_contains_any(
        normalized,
        {"get", "include", "included", "value", "what do i", "what does"},
    ):
        return candidate(
            "campaign_depth_growth_plan_answered",
            "price",
            "It adds priority routing, reminders, duplicate checks, Slack alerts, and handoff review when missed callbacks cost time. Which gap shows up more: callbacks, duplicates, or visibility?",
        )
    if normalized_contains_any(normalized, {"manual", "spreadsheet", "tracking leads manually", "track leads manually"}):
        return candidate(
            "campaign_depth_manual_tracking_answered",
            "fit",
            "That breaks when ownership changes. RouteSignal keeps the lead, callback, reminder, and handoff status in one workflow. Where does it break first today?",
        )
    if normalized_contains_any(normalized, {"small team", "small teams"}):
        return candidate(
            "campaign_depth_small_team_fit_answered",
            "fit",
            "Start with Starter if missed follow-up is occasional. Use Growth only when routing saves real time. Are missed callbacks occasional, or frequent enough to automate?",
        )
    if normalized_contains_any(
        normalized,
        {
            "what does your product",
            "what does the product",
            "what do you do",
            "what does it do",
            "what is your product",
            "product actually do",
        },
    ):
        return candidate(
            "campaign_depth_product_explanation_answered",
            "details",
            (
                knowledge.get("short_product_explanation")
                or "RouteSignal CRM routes leads, captures follow-up tasks, and shows handoff status."
            )
            + " Where does follow-up break first today: routing, reminders, or handoff review?",
        )
    if normalized_contains_any(normalized, {"workflow include", "workflow includes", "what is included", "included in the workflow"}):
        return candidate(
            "campaign_depth_workflow_scope_answered",
            "details",
            "It covers lead capture, qualification, routing, reminders, and handoff review. Which part is weakest today: capture, routing, reminders, or handoff review?",
        )
    return None


def language_for_campaign(campaign_id: str, cases_path: Path) -> str:
    return str(load_campaign(campaign_id, cases_path).get("language") or "en").lower()


def response_asked_price_choice(response: str) -> bool:
    lowered = response.lower()
    return (
        "bigger concern the monthly price" in lowered
        or "main concern price" in lowered
        or "preis, die bedingungen" in lowered
        or "preis selbst oder darum" in lowered
    )


def response_asked_main_focus_choice(response: str) -> bool:
    lowered = response.lower()
    return (
        "main question about price, fit, timing, or exact product details" in lowered
        or "price, fit, timing" in lowered
        or "main concern whether this is relevant for your situation, the price, or the timing" in lowered
        or "passung, zeitpunkt oder genaue details" in lowered
    )


def response_reopens_focus_menu(response: str) -> bool:
    return response_asked_main_focus_choice(response) or response_asked_price_choice(response)


def focus_menu_count(turns: list[dict]) -> int:
    return sum(
        1
        for turn in turns
        if response_reopens_focus_menu(str((turn.get("summary") or {}).get("final_response") or ""))
    )


def previous_responses(turns: list[dict]) -> set[str]:
    return {
        str((turn.get("summary") or {}).get("final_response") or "").strip()
        for turn in turns
        if str((turn.get("summary") or {}).get("final_response") or "").strip()
    }


def focus_turn_count(turns: list[dict], focus: str) -> int:
    return sum(
        1
        for turn in turns
        if str((turn.get("continuity") or {}).get("dialogue_focus") or "") == focus
    )


def dialogue_focus_from_turns(turns: list[dict]) -> str | None:
    for turn in reversed(turns):
        continuity = turn.get("continuity") or {}
        explicit_focus = continuity.get("dialogue_focus")
        if explicit_focus:
            return str(explicit_focus)
        reason = str(continuity.get("reason") or "")
        if not continuity.get("applied") and not reason.startswith(("short_answer_selected_", "focus_shift_to_", "resolved_")):
            continue
        response = str((turn.get("summary") or {}).get("final_response") or "").lower()
        if "selected_price" in reason or "focus only on price" in response or "stay on price" in response:
            return "price"
        if "selected_terms" in reason or "review the terms clearly" in response or "terms clearly first" in response:
            return "terms"
        if "selected_effort" in reason or "worth your time" in response or "worth the review" in response:
            return "effort"
        if "selected_fit" in reason or "focus on fit" in response:
            return "fit"
        if "selected_timing" in reason or "keep timing first" in response:
            return "timing"
        if "selected_details" in reason or "product details" in response:
            return "details"
    return None


def continuity_text(language: str, focus: str, *, persisted: bool = False) -> str:
    german = language.startswith("de")
    if focus == "price":
        if german:
            return (
                "Verstanden. Wir bleiben beim Preis: Sinnvoll ist ein klarer Vergleich von Kosten und Bedingungen, "
                "ohne in diesem Anruf eine Entscheidung zu verlangen."
            )
        if persisted:
            return live_demo_price_answer(language)
        return live_demo_price_answer(language)
    if focus == "terms":
        if german:
            if persisted:
                return "Dann bleiben wir bei den Bedingungen. Der naechste sinnvolle Schritt ist, die Laufzeit, den Umfang und die Ausstiegsmoeglichkeit schriftlich zu vergleichen."
            return "Verstanden. Dann pruefen wir zuerst die Bedingungen klar, bevor ueberhaupt ein Wechsel im Raum steht."
        if persisted:
            return "Terms should be written first: contract length, scope, and exit path. No commitment on this call."
        return "Terms should be checked in writing first: length, scope, and exit path. No commitment on this call."
    if focus == "effort":
        if german:
            if persisted:
                return "Dann machen wir den Aufwand konkret: Die Durchsicht lohnt sich nur, wenn Rueckrufe oder Nachverfolgung heute wirklich Zeit kosten."
            return "Verstanden. Dann pruefen wir zuerst, ob sich die Durchsicht fuer Ihre Zeit lohnt; wenn nicht, gibt es keinen Grund zu draengen."
        if persisted:
            return "The effort test is simple: does missed follow-up cost more time than this review? If not, stop here."
        return "The effort test is simple: does missed follow-up cost more time than this review? If not, stop here."
    if focus == "fit":
        if german:
            if persisted:
                return "Dann bleiben wir bei der Passung. Entscheidend ist, ob Rueckruf- oder Nachverfolgungsarbeit in Ihrem aktuellen Ablauf wirklich offen bleibt."
            return "Verstanden. Dann geht es zuerst um Passung: ob das Problem in Ihrer Situation wirklich existiert, bevor wir ueber einen naechsten Schritt sprechen."
        if persisted:
            return "Fit depends on a real workflow gap: missed leads, callbacks, or handoffs. If that is not happening, stop here."
        return "Fit depends on a real workflow gap: missed leads, callbacks, or handoffs. If that is not happening, stop here."
    if focus == "timing":
        if german:
            if persisted:
                return "Dann bleibt der Zeitpunkt der Engpass. Ich wuerde es bei einer schriftlichen Zusammenfassung oder einem spaeteren Rueckruf belassen."
            return "Verstanden. Dann steht der Zeitpunkt im Vordergrund. Heute muss nichts entschieden werden; hoechstens eine kurze schriftliche Zusammenfassung oder ein spaeterer Rueckruf."
        if persisted:
            return "If timing is the blocker, use a written summary or later callback. No decision now."
        return "If timing is the blocker, use a written summary or later callback. No decision now."
    if focus == "details":
        if german:
            if persisted:
                return "Dann bleiben wir bei den Details. Ich wuerde nur klaeren, was der Workflow abdeckt, was er nicht abdeckt und was ein Spezialist pruefen muss."
            return "Verstanden. Dann bleiben wir bei den Produktdetails: was der Workflow umfasst, was er nicht umfasst, und was ein Spezialist pruefen sollte."
        if persisted:
            return "The workflow scope is lead routing, follow-up, and handoff review. Exact integrations need verified checks."
        return "The workflow scope is lead routing, follow-up, and handoff review. Exact integrations need verified checks."
    return "Thanks. I will keep the next step narrow and avoid repeating the same question."


def focus_followup_text(language: str, focus: str, normalized: str) -> str:
    german = language.startswith("de")
    asks_for_explanation = normalized_contains_any(
        normalized,
        {"explain", "tell me", "what does", "what is", "what's", "what would", "how does", "include", "includes"},
    )
    asks_for_recommendation = normalized_contains_any(
        normalized,
        {"recommend", "what do you recommend", "what would you choose", "what should i choose"},
    )
    agrees_to_continue = normalized_contains_any(
        normalized,
        {"do that", "let's do that", "lets do that", "all right", "okay", "ok", "yes", "sure", "sounds good"},
    )
    if focus == "price":
        if asks_for_recommendation:
            if german:
                return live_demo_price_answer(language)
            return live_demo_price_answer(language)
        if asks_for_explanation:
            if german:
                return live_demo_price_answer(language)
            return live_demo_price_answer(language)
        if agrees_to_continue:
            if german:
                return live_demo_price_answer(language)
            return live_demo_price_answer(language)
    if focus == "effort":
        if asks_for_explanation:
            if german:
                return "Die Aufwandfrage ist konkret: Lohnt sich die Durchsicht nur dann, wenn Rueckrufe oder Nachverfolgung heute wirklich Zeit kosten?"
            return "The effort question is concrete: is a review worth it only if missed callbacks or follow-up work are costing time today?"
        if agrees_to_continue:
            if german:
                return "Gut, dann pruefen wir nur den Aufwand. Wenn der Zeitverlust heute nicht klar ist, sollte ich keinen naechsten Schritt draengen."
            return "Check effort only: is missed follow-up costing enough time to justify a review? If not, stop here."
    if focus == "details":
        if asks_for_explanation:
            if german:
                return "Bei den Details geht es hier um Lead-Routing und Nachverfolgung. Was genau integriert wird, sollte ein Spezialist pruefen."
            return "The workflow scope is lead routing, follow-up, and handoff review. Exact integrations need verified checks."
        if agrees_to_continue:
            if german:
                return "Gut, dann bleiben wir bei den Details: was der Workflow abdeckt, was offen bleibt und was ein Spezialist pruefen sollte."
            return "Check scope only: what the workflow covers, what remains open, and what needs verified review."
    if focus == "fit":
        if asks_for_explanation:
            if german:
                return "Bei der Passung geht es darum, ob Lead-Routing oder Nachverfolgung in Ihrem aktuellen Ablauf wirklich ein Problem ist."
            return "Fit depends on a real workflow gap: missed leads, callbacks, or handoffs. If that is not happening, stop here."
        if agrees_to_continue:
            if german:
                return "Gut, dann bleiben wir bei der Passung und pruefen nur, ob das Problem in Ihrem Ablauf wirklich existiert."
            return "Check fit only: are leads, callbacks, or handoffs getting missed today? If not, stop here."
    if focus == "timing":
        if asks_for_explanation or agrees_to_continue:
            return continuity_text(language, "timing", persisted=True)
    return continuity_text(language, focus, persisted=True)


def progressive_focus_text(language: str, focus: str, normalized: str, step: int) -> str:
    german = language.startswith("de")
    variants = {
        "price": [
            (
                live_demo_price_answer(language)
                if not german
                else "Zum Preis kann ich nur sauber bleiben: Kosten, Bedingungen und Umfang vergleichen; genaue freigegebene Preise sollten schriftlich oder vom Spezialisten kommen."
            ),
            (
                "Starter covers basic lead capture and routing. Growth adds priority routing, reminders, and handoff review."
                if not german
                else "Die konkrete Preisfrage ist: was enthalten ist, welche Laufzeit gilt und ob der naechste Schritt unverbindlich bleibt."
            ),
            (
                "Use Starter for basic routing. Use Growth only when missed callbacks or slow handoffs cost time."
                if not german
                else "Wenn der Preis weiter der Engpass ist, wuerde ich nicht weiter verkaufen, sondern einen schriftlichen Preis- und Umfangsvergleich nutzen."
            ),
        ],
        "fit": [
            (
                "Fit depends on a real workflow gap: missed leads, callbacks, or handoffs. If that is not happening, stop here."
                if not german
                else "Bei der Passung geht es darum, ob Lead-Routing oder Nachverfolgung in Ihrem aktuellen Ablauf wirklich ein Problem ist."
            ),
            (
                "The practical fit check is whether inbound leads, callbacks, or handoffs get missed today."
                if not german
                else "Die naechste Passungsfrage ist praktisch: Bleiben heute Leads, Rueckrufe oder Uebergaben liegen?"
            ),
            (
                "If that problem is real, a verified workflow review may be useful. If not, stop here."
                if not german
                else "Wenn dieses Problem real ist, kann ein Spezialist die Passung pruefen; wenn nicht, gibt es keinen Grund weiterzumachen."
            ),
            (
                "The yes-or-no is whether missed handoffs justify even a short workflow review."
                if not german
                else "Die praktische Ja-Nein-Frage ist, ob verpasste Uebergaben oft genug passieren, um eine kurze Spezialistenpruefung zu rechtfertigen."
            ),
            (
                "If fit stays unclear after that, stop at a written summary."
                if not german
                else "Wenn die Passung danach noch unklar ist, wuerde ich bei einer schriftlichen Zusammenfassung stoppen, statt live weiterzudraengen."
            ),
        ],
        "details": [
            (
                "The workflow scope is lead routing, follow-up, and handoff review. Exact integrations need verified checks."
                if not german
                else "Bei den Details geht es um Lead-Routing und Nachverfolgung. Genaue Integrationen sollte ein Spezialist pruefen."
            ),
            (
                "Safe product detail means scope only: routing inbound leads, follow-up work, and handoff review."
                if not german
                else "Das sichere Produktdetail ist der Umfang: Lead-Routing, Nachverfolgung und Uebergabepruefung; Integrationen sollte ich nicht erfinden."
            ),
            (
                "For details beyond that, use verified review instead of live guessing."
                if not german
                else "Wenn Sie darueber hinaus Details wollen, ist eine Spezialistenpruefung besser als Live-Raten."
            ),
        ],
        "effort": [
            (
                "The effort test is simple: does missed follow-up cost more time than this review? If not, stop here."
                if not german
                else "Die Aufwandfrage ist konkret: Lohnt sich die Durchsicht nur, wenn Rueckrufe oder Nachverfolgung heute Zeit kosten?"
            ),
            (
                "If the review takes more time than the problem costs, stop here."
                if not german
                else "Wenn die Durchsicht mehr Zeit kostet als das Problem selbst, sollte man sie nicht draengen."
            ),
            (
                "The next check is whether missed follow-up justifies even a short review."
                if not german
                else "Die naechste sinnvolle Frage ist einfach: Gibt es genug verpasste Nachverfolgung fuer eine kurze Pruefung?"
            ),
        ],
        "terms": [
            (
                "Terms should be written first: contract length, scope, and exit path. No commitment on this call."
                if not german
                else "Dann bleiben wir bei den Bedingungen: Laufzeit, Umfang und Ausstieg sollten zuerst schriftlich verglichen werden."
            ),
            (
                "The terms check comes before any decision: length, included scope, and exit path."
                if not german
                else "Die Bedingungspruefung kommt vor jeder Entscheidung: Laufzeit, Umfang und was passiert, wenn es nicht nuetzt."
            ),
        ],
        "timing": [
            (
                "If timing is the blocker, use a written summary or later callback. No decision now."
                if not german
                else "Dann bleibt der Zeitpunkt der Engpass. Ich wuerde es bei schriftlicher Zusammenfassung oder spaeterem Rueckruf belassen."
            ),
            (
                "If now is not the right time, use a later callback or written summary."
                if not german
                else "Wenn jetzt nicht der richtige Zeitpunkt ist, bleibt nur ein spaeterer Rueckruf oder eine schriftliche Zusammenfassung."
            ),
        ],
    }
    options = variants.get(focus) or [continuity_text(language, focus, persisted=True)]
    return options[min(step, len(options) - 1)]


def unique_progressive_focus_text(language: str, focus: str, normalized: str, step: int, seen: set[str]) -> str:
    for offset in range(4):
        candidate = progressive_focus_text(language, focus, normalized, step + offset)
        if candidate not in seen:
            return candidate
    fallback = progressive_focus_text(language, focus, normalized, step)
    suffix = (
        " The next concrete question is whether that is worth verified review."
        if not language.startswith("de")
        else " Die naechste konkrete Frage ist, ob sich dafuer eine Spezialistenpruefung lohnt."
    )
    return fallback + suffix


def duplicate_response_repair(transcript: str, session_state: dict | None, language: str, generated_response: str) -> dict:
    turns = list((session_state or {}).get("turns") or [])
    response = generated_response.strip()
    if is_live_demo_price_answer(response):
        return {"applied": False, "reason": "factual_price_repetition_allowed"}
    if not response or response not in previous_responses(turns):
        return {"applied": False, "reason": "no_duplicate_response_detected"}
    normalized = normalize_text(transcript)
    focus = focus_from_transcript(normalized) or dialogue_focus_from_turns(turns)
    if focus:
        return {
            "applied": True,
            "reason": f"duplicate_response_prevented_with_{focus}_progression",
            "dialogue_focus": focus,
            "candidate_response": unique_progressive_focus_text(
                language,
                focus,
                normalized,
                focus_turn_count(turns, focus),
                previous_responses(turns),
            ),
        }
    text = (
        "I already answered that at a high level. Give me one concrete follow-up and I will answer that directly."
        if not language.startswith("de")
        else "Das habe ich auf hoher Ebene bereits beantwortet. Nennen Sie eine konkrete Folgefrage, dann antworte ich direkt darauf."
    )
    return {
        "applied": True,
        "reason": "duplicate_response_prevented_without_clear_focus",
        "candidate_response": text,
    }


def current_focus_followup_response(normalized: str, resolved_focus: str | None, language: str) -> dict | None:
    if not resolved_focus:
        return None
    continuation_signals = {
        "do that",
        "lets do that",
        "let s do that",
        "all right",
        "okay",
        "ok",
        "yes",
        "sure",
        "sounds good",
        "go ahead",
        "explain",
        "explain that",
        "explain to me",
        "tell me",
        "what does",
        "what is",
        "what s",
        "what would",
        "how does",
        "include",
        "includes",
        "workflow include",
        "workflow includes",
        "workflow",
        "recommend",
        "what do you recommend",
        "what should i choose",
    }
    if not normalized_contains_any(normalized, continuation_signals):
        return None
    return {
        "applied": True,
        "reason": f"resolved_{resolved_focus}_focus_followup",
        "dialogue_focus": resolved_focus,
        "candidate_response": focus_followup_text(language, resolved_focus, normalized),
    }


def focus_from_transcript(normalized: str) -> str | None:
    price_deferred = normalized_contains_any(
        normalized,
        {
            "price later",
            "price later on",
            "talk about the price later",
            "talk about price later",
        },
    )
    if normalized in {"price", "the price", "cost", "costs", "money", "monthly price", "preis", "kosten"}:
        return "price"
    if normalized in {"terms", "contract terms", "conditions", "bedingungen", "vertragsbedingungen"}:
        return "terms"
    if normalized in {"effort", "worth it", "worth the effort", "time", "aufwand", "lohnt sich", "zeit"}:
        return "effort"
    if normalized in {"fit", "relevance", "relevant", "if it fits", "passung", "passt"}:
        return "fit"
    if normalized in {"timing", "later", "not now", "time", "zeitpunkt", "spaeter"}:
        return "timing"
    if normalized in {"details", "product details", "exact details", "plan details", "details first", "produktdetails"}:
        return "details"
    if normalized_contains_any(
        normalized,
        {
            "worth my time",
            "worth the time",
            "worth my effort",
            "worth the effort",
            "reviewing options is worth",
            "viewing options is worth",
            "whether reviewing",
            "whether a viewing",
            "if this is worth",
            "if it is worth",
        },
    ):
        return "effort"
    if normalized_contains_any(
        normalized,
        {
            "start with the price",
            "start with price",
            "about price",
            "about the price",
            "talk about the price",
            "talk about price",
            "the price is the problem",
            "price is the problem",
            "main concern is price",
            "price first",
            "cost first",
            "monthly price",
            "too expensive",
            "expensive",
            "budget",
            "price concern",
        },
    ) and not price_deferred:
        return "price"
    if normalized_contains_any(
        normalized,
        {
            "contract terms",
            "the terms",
            "terms first",
            "conditions first",
            "main concern is terms",
        },
    ):
        return "terms"
    if normalized_contains_any(
        normalized,
        {
            "talk about the fit",
            "talk about fit",
            "the fit",
            "fit is good",
            "if the fit is good",
            "whether it fits",
            "if it fits",
            "fit our workflow",
            "fits our workflow",
            "fit my situation",
            "relevant for my situation",
            "relevant for the situation",
            "relevant for us",
            "my situation",
            "the situation",
            "relevant for us",
            "relevant to us",
        },
    ):
        return "fit"
    if normalized_contains_any(
        normalized,
        {
            "not now",
            "call me later",
            "callback later",
            "timing first",
            "bad timing",
            "need time",
            "still need time",
        },
    ):
        return "timing"
    if normalized_contains_any(
        normalized,
        {
            "exact product details",
            "product details",
            "plan details",
            "what is included",
            "workflow includes",
            "workflow include",
            "what does the workflow",
            "what does workflow",
            "details first",
        },
    ):
        return "details"
    return None


def anti_loop_response(transcript: str, session_state: dict | None, language: str, generated_response: str) -> dict:
    turns = list((session_state or {}).get("turns") or [])
    if not response_reopens_focus_menu(generated_response) or focus_menu_count(turns) == 0:
        return {"applied": False, "reason": "no_menu_loop_detected"}

    normalized = normalize_text(transcript)
    resolved_focus = dialogue_focus_from_turns(turns)
    selected_focus = focus_from_transcript(normalized)
    focus = selected_focus or resolved_focus
    if focus:
        return {
            "applied": True,
            "reason": f"menu_loop_prevented_with_{focus}_focus",
            "dialogue_focus": focus,
            "candidate_response": focus_followup_text(language, focus, normalized),
        }

    text = (
        "I only caught part of that. Please repeat the question in one sentence."
        if not language.startswith("de")
        else "Ich habe nur einen Teil verstanden. Bitte wiederholen Sie die Frage in einem Satz."
    )
    return {
        "applied": True,
        "reason": "menu_loop_prevented_without_clear_focus",
        "candidate_response": text,
    }


def continuity_response(transcript: str, session_state: dict | None, campaign: dict) -> dict:
    language = str(campaign.get("language") or "en")
    normalized = normalize_text(transcript)
    turns = list((session_state or {}).get("turns") or [])
    previous = turns[-1] if turns else {}
    previous_summary = previous.get("summary") or {}
    previous_response = str(previous_summary.get("final_response") or "")

    resolved_focus = dialogue_focus_from_turns(turns)
    selected_focus = focus_from_transcript(normalized)
    if looks_like_asr_fragment(normalized, selected_focus):
        return {
            "applied": True,
            "reason": "asr_fragment_repair",
            "dialogue_focus": resolved_focus,
            "candidate_response": asr_fragment_response(language),
        }
    if not turns and is_opening_greeting(normalized):
        return {
            "applied": True,
            "reason": "opening_greeting_answered",
            "candidate_response": opening_greeting_response(language),
        }
    if selected_focus and resolved_focus and selected_focus != resolved_focus:
        return {
            "applied": True,
            "reason": f"focus_shift_to_{selected_focus}_from_{resolved_focus}",
            "dialogue_focus": selected_focus,
            "candidate_response": continuity_text(language, selected_focus),
        }
    current_focus_followup = current_focus_followup_response(normalized, resolved_focus, language)
    if current_focus_followup:
        return current_focus_followup
    if resolved_focus == "price" and normalized_contains_any(
        normalized,
        {"price", "cost", "too expensive", "monthly price", "budget", "money", "preis", "kosten", "zu teuer"},
    ):
        return {
            "applied": True,
            "reason": "resolved_price_focus_persisted",
            "dialogue_focus": "price",
            "candidate_response": continuity_text(language, "price", persisted=True),
        }
    if resolved_focus == "fit" and normalized_contains_any(
        normalized,
        {"fit", "relevant", "situation", "workflow", "problem", "passung", "passt"},
    ):
        return {
            "applied": True,
            "reason": "resolved_fit_focus_persisted",
            "dialogue_focus": "fit",
            "candidate_response": continuity_text(language, "fit", persisted=True),
        }
    if resolved_focus == "timing" and normalized_contains_any(
        normalized,
        {"timing", "later", "not now", "callback", "time", "zeitpunkt", "spaeter"},
    ):
        return {
            "applied": True,
            "reason": "resolved_timing_focus_persisted",
            "dialogue_focus": "timing",
            "candidate_response": continuity_text(language, "timing", persisted=True),
        }
    if resolved_focus == "effort" and normalized_contains_any(
        normalized,
        {"worth", "worth my time", "worth the effort", "reviewing options", "viewing options", "effort", "time"},
    ):
        return {
            "applied": True,
            "reason": "resolved_effort_focus_persisted",
            "dialogue_focus": "effort",
            "candidate_response": continuity_text(language, "effort", persisted=True),
        }
    if resolved_focus == "terms" and normalized_contains_any(
        normalized,
        {"terms", "contract terms", "conditions", "bedingungen", "vertragsbedingungen"},
    ):
        return {
            "applied": True,
            "reason": "resolved_terms_focus_persisted",
            "dialogue_focus": "terms",
            "candidate_response": continuity_text(language, "terms", persisted=True),
        }
    if resolved_focus == "details" and normalized_contains_any(
        normalized,
        {"details", "product details", "plan details", "included", "exact product"},
    ):
        return {
            "applied": True,
            "reason": "resolved_details_focus_persisted",
            "dialogue_focus": "details",
            "candidate_response": continuity_text(language, "details", persisted=True),
        }

    if selected_focus and response_asked_price_choice(previous_response) and selected_focus in {"price", "terms", "effort"}:
        return {
            "applied": True,
            "reason": f"short_answer_selected_{selected_focus}_after_price_prompt",
            "dialogue_focus": selected_focus,
            "candidate_response": continuity_text(language, selected_focus),
        }
    if selected_focus and response_asked_main_focus_choice(previous_response):
        return {
            "applied": True,
            "reason": f"short_answer_selected_{selected_focus}_after_main_focus_prompt",
            "dialogue_focus": selected_focus,
            "candidate_response": continuity_text(language, selected_focus),
        }
    if normalized in {"yes", "yeah", "yep", "sure", "ok", "okay"} and response_asked_main_focus_choice(previous_response):
        text = (
            "I need one focus to make this useful: price, fit, timing, or exact product details."
            if not language.startswith("de")
            else "Ich brauche einen Fokus, damit es hilfreich ist: Preis, Passung, Zeitpunkt oder genaue Produktdetails."
        )
        return {
            "applied": True,
            "reason": "affirmative_after_main_focus_prompt_needs_specific_focus",
            "candidate_response": text,
        }
    if previous_summary.get("sales_difficulty") == "autonomy-check" and normalized_contains_any(
        normalized,
        {"need time", "still need time", "not now", "later", "callback", "do not rush", "dont rush"},
    ):
        return {
            "applied": True,
            "reason": "autonomy_followup_kept_low_pressure",
            "dialogue_focus": "timing",
            "candidate_response": continuity_text(language, "timing"),
        }
    if previous_summary.get("sales_difficulty") == "existing-provider-gap" and normalized_contains_any(
        normalized,
        {"routing", "follow up", "followup", "callback", "does not cover", "misses", "gap"},
    ):
        text = (
            "Then that is the gap to check: whether routing, callbacks, or follow-up work are still slipping through. I can keep this to a written comparison."
            if not language.startswith("de")
            else "Dann ist genau diese Luecke der Punkt: ob Routing, Rueckrufe oder Nachverfolgung noch liegen bleiben. Ich kann das auf einen schriftlichen Vergleich begrenzen."
        )
        return {
            "applied": True,
            "reason": "provider_gap_followup_answered",
            "dialogue_focus": "provider_gap",
            "candidate_response": text,
        }

    campaign_depth = english_live_demo_campaign_response(normalized, campaign)
    if campaign_depth:
        return campaign_depth

    if selected_focus and not resolved_focus:
        return {
            "applied": True,
            "reason": f"initial_{selected_focus}_focus_selected" if not turns else f"explicit_{selected_focus}_focus_selected",
            "dialogue_focus": selected_focus,
            "candidate_response": continuity_text(language, selected_focus),
        }

    return {"applied": False, "reason": "no_session_continuity_match"}


def build_turn_packet(
    *,
    transcript: str,
    campaign_id: str,
    stage: str,
    input_type: str,
    silence_count: int,
    cases_path: Path,
    private_out: Path,
    live_tts: bool,
    force_key_missing: bool,
    timeout_seconds: float,
    session_id: str | None = None,
    session_state: dict | None = None,
    asr_confidence: float | None = None,
    voice_turn_state: str | None = None,
) -> dict:
    start = time.perf_counter()
    campaign = load_campaign(campaign_id, cases_path)
    language = str(campaign.get("language") or "en")
    quality_gate = evaluate_asr_quality(transcript, asr_confidence)
    if not quality_gate["accepted"]:
        continuity = repair_response_for_quality_gate(language, quality_gate)
    else:
        continuity = session_policy.continuity_response(transcript, session_state, campaign)
    guarded = build_guarded_response_packet(
        campaign=campaign,
        stage=stage,
        input_type=input_type,
        transcript=transcript,
        silence_count=silence_count,
        candidate_response_override=continuity.get("candidate_response") if continuity.get("applied") else None,
        **live_demo_retrieval_kwargs(),
        align_decision_trace=True,
    )
    if not continuity.get("applied"):
        anti_loop = session_policy.anti_loop_response(
            transcript,
            session_state,
            str(campaign.get("language") or "en"),
            str(guarded.get("final_response") or ""),
        )
        if anti_loop.get("applied"):
            continuity = anti_loop
            guarded = build_guarded_response_packet(
                campaign=campaign,
                stage=stage,
                input_type=input_type,
                transcript=transcript,
                silence_count=silence_count,
                candidate_response_override=anti_loop.get("candidate_response"),
                **live_demo_retrieval_kwargs(),
                align_decision_trace=True,
            )
    duplicate_repair = session_policy.duplicate_response_repair(
        transcript,
        session_state,
        str(campaign.get("language") or "en"),
        str(guarded.get("final_response") or ""),
    )
    if duplicate_repair.get("applied"):
        continuity = duplicate_repair
        guarded = build_guarded_response_packet(
            campaign=campaign,
            stage=stage,
            input_type=input_type,
            transcript=transcript,
            silence_count=silence_count,
            candidate_response_override=duplicate_repair.get("candidate_response"),
            **live_demo_retrieval_kwargs(),
            align_decision_trace=True,
        )
    conversation_memory = session_policy.build_conversation_memory(
        session_state,
        transcript,
        str(guarded.get("final_response") or ""),
        continuity,
    )
    stability_guard = session_policy.pre_speech_conversation_stability_guard(
        transcript,
        session_state,
        str(campaign.get("language") or "en"),
        str(guarded.get("final_response") or ""),
        conversation_memory,
    )
    if stability_guard.get("applied"):
        continuity = stability_guard
        guarded = build_guarded_response_packet(
            campaign=campaign,
            stage=stage,
            input_type=input_type,
            transcript=transcript,
            silence_count=silence_count,
            candidate_response_override=stability_guard.get("candidate_response"),
            **live_demo_retrieval_kwargs(),
            align_decision_trace=True,
        )
        conversation_memory = session_policy.build_conversation_memory(
            session_state,
            transcript,
            str(guarded.get("final_response") or ""),
            continuity,
        )
    guarded = apply_live_session_decision_overrides(guarded, continuity)
    voice_packet = attach_runtime_voice_delivery(guarded, campaign, provider_key="elevenlabs")
    tts_packet = attach_runtime_tts_delivery(
        voice_packet,
        provider_key="elevenlabs",
        live=live_tts,
        force_key_missing=force_key_missing,
        audio_dir=private_out / "audio",
        timeout_seconds=timeout_seconds,
        command_name="scripts/run_live_demo_001_agent_voice_call.py",
        voice_consistency_mode="live-demo-stable",
    )
    summary = decision_summary(tts_packet)
    if quality_gate["accepted"]:
        deterministic_reasoning = reason_about_turn(transcript, session_state, campaign, mode="baseline")
    else:
        deterministic_reasoning = validate_reasoning_packet(
            {
                "dialogue_act": "asr_fragment",
                "buyer_intent": "repair_asr",
                "resolved_topic": "asr_quality",
                "sales_stage": "repair",
                "response_strategy": "repeat_request",
                "must_include": ["repeat request"],
                "must_avoid": ["guessing buyer intent from low-confidence ASR"],
                "safety_boundary": "asr_quality_boundary",
                "confidence": float(quality_gate.get("confidence") or 0.0),
            }
        )
    async_enrichment = build_async_enrichment_request(
        transcript=transcript,
        context=build_reasoning_context(transcript, session_state, campaign),
        deterministic_reasoning=deterministic_reasoning,
        case_goal="LIVE-DEMO-001 private evidence only; do not influence current spoken response.",
        customer_response_text=summary["final_response"],
        response_packet_id=f"{LIVE_DEMO_ID}:{session_id or 'no-session'}:{len((session_state or {}).get('turns') or []) + 1}",
    )
    return {
        "live_demo_id": LIVE_DEMO_ID,
        "mode": "live-tts" if live_tts else "dry-run",
        "campaign_id": campaign_id,
        "session_id": session_id,
        "session_turn_index": len((session_state or {}).get("turns") or []) + 1,
        "stage": stage,
        "input_type": input_type,
        "transcript": transcript,
        "asr": {
            "provider": "browser-speech-recognition",
            "audio_uploaded_to_python_server": False,
            "browser_vendor_may_process_audio": True,
            "transcript_sent_to_python_server": True,
            "confidence": asr_confidence,
            "quality_gate": quality_gate,
        },
        "turn_taking": {
            **turn_taking_packet(voice_turn_state),
            "browser_asr_policy": realtime_turn_taking_policy(),
        },
        "provider_agent_used": False,
        "durable_provider_agent_created": False,
        "voice_cloning_used": False,
        "runtime_behavior_changed": False,
        "opens_prod_102": False,
        "demo_session_continuity": continuity,
        "demo_conversation_memory": conversation_memory,
        "demo_conversation_stability_guard": stability_guard,
        "dialogue_reasoner_async_enrichment": async_enrichment,
        "packet": tts_packet,
        "summary": summary,
        "audio_url": audio_url_for_packet(tts_packet),
        "latency": {
            "server_total_ms": elapsed_ms(start),
            "browser_asr_ms": None,
        },
    }


def render_html(metadata: dict) -> str:
    metadata_json = json.dumps(metadata, ensure_ascii=False)
    title = "LIVE-DEMO-001 Agent Voice Call"
    live_label = "ElevenLabs live voice enabled" if metadata["tts"]["live_tts_enabled"] else "ElevenLabs dry-run"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    :root {{
      --bg: #f7f4ee;
      --panel: #fffdfa;
      --ink: #18211f;
      --muted: #5d6965;
      --line: #d8d0c2;
      --accent: #0f766e;
      --warn: #a24f2f;
      --soft: #e9f3f1;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--ink);
      font-family: Arial, Helvetica, sans-serif;
    }}
    main {{
      width: min(1120px, calc(100vw - 28px));
      margin: 0 auto;
      padding: 24px 0 36px;
    }}
    header {{
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 18px;
      border-bottom: 1px solid var(--line);
      padding-bottom: 16px;
    }}
    h1 {{ margin: 0; font-size: 1.8rem; letter-spacing: 0; }}
    .badge {{ padding: 8px 10px; background: var(--soft); border: 1px solid var(--line); border-radius: 6px; font-weight: 700; }}
    .grid {{ display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 16px; margin-top: 18px; }}
    section {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 16px; }}
    h2 {{ margin: 0 0 10px; font-size: 0.95rem; }}
    textarea, pre {{
      width: 100%;
      min-height: 138px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 12px;
      background: white;
      color: var(--ink);
      font: 0.95rem/1.5 Consolas, "Cascadia Mono", monospace;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }}
    .controls {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }}
    button, select {{
      min-height: 38px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 8px 11px;
      font: 700 0.93rem Arial, Helvetica, sans-serif;
    }}
    button {{ background: var(--accent); color: white; cursor: pointer; border-color: var(--accent); }}
    button.secondary {{ background: #27312d; border-color: #27312d; }}
    button.warn {{ background: var(--warn); border-color: var(--warn); }}
    button:disabled {{ opacity: 0.5; cursor: not-allowed; }}
    label {{ display: flex; gap: 8px; align-items: center; color: var(--muted); line-height: 1.4; }}
    audio {{ width: 100%; margin-top: 10px; }}
    .full {{ grid-column: 1 / -1; }}
    .status {{ margin-top: 10px; color: var(--muted); }}
    @media (max-width: 820px) {{ .grid {{ grid-template-columns: 1fr; }} header {{ align-items: start; flex-direction: column; }} }}
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>LIVE-DEMO-001 Agent Voice Call</h1>
        <div class="status">Brain: repo runtime. Voice: ElevenLabs TTS. ASR: browser speech recognition.</div>
      </div>
      <div class="badge">{html.escape(live_label)}</div>
    </header>

    <div class="grid">
      <section>
        <h2>Your Turn</h2>
        <label><input id="consent" type="checkbox"> I consent to using my microphone for this local demo.</label>
        <div class="controls">
          <select id="campaign"></select>
          <select id="language">
            <option value="en-US" selected>English</option>
            <option value="de-DE">German</option>
            <option value="tr-TR">Turkish</option>
          </select>
          <button id="listen" type="button">Start Conversation</button>
          <button id="stop" class="secondary" type="button">Stop Conversation</button>
          <button id="send" class="warn" type="button">Send To Agent</button>
        </div>
        <textarea id="transcript" placeholder="Speak, or type a test turn here."></textarea>
        <div id="status" class="status">Ready.</div>
      </section>

      <section>
        <h2>Agent Response</h2>
        <pre id="response">Waiting for a turn.</pre>
        <audio id="audio" controls></audio>
        <div class="controls">
          <button id="interruptAgent" class="warn" type="button">Interrupt Agent</button>
          <button id="browserSpeak" class="secondary" type="button">Browser Fallback Voice</button>
        </div>
      </section>

      <section>
        <h2>Decision</h2>
        <pre id="decision">No decision yet.</pre>
      </section>

      <section>
        <h2>Provider Boundary</h2>
        <pre id="boundary">No provider call yet.</pre>
      </section>

      <section class="full">
        <h2>Conversation Transcript</h2>
        <div class="controls">
          <button id="downloadTranscriptJson" class="secondary" type="button">Download JSON</button>
          <button id="downloadTranscriptText" class="secondary" type="button">Download TXT</button>
        </div>
        <pre id="conversationTranscript">No turns yet.</pre>
        <details>
          <summary>Diagnostics</summary>
          <pre id="conversationDiagnostics">No diagnostics yet.</pre>
        </details>
      </section>

      <section class="full">
        <h2>Turn Packet</h2>
        <pre id="packet">No packet yet.</pre>
      </section>
    </div>
  </main>

  <script>
    const metadata = {metadata_json};
    const AGENT_OPEN_TRANSCRIPT = "__agent_open__";
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const consent = document.querySelector("#consent");
    const campaign = document.querySelector("#campaign");
    const language = document.querySelector("#language");
    const listen = document.querySelector("#listen");
    const stop = document.querySelector("#stop");
    const send = document.querySelector("#send");
    const transcript = document.querySelector("#transcript");
    const responseBox = document.querySelector("#response");
    const decision = document.querySelector("#decision");
    const boundary = document.querySelector("#boundary");
    const packet = document.querySelector("#packet");
    const conversationTranscriptBox = document.querySelector("#conversationTranscript");
    const conversationDiagnosticsBox = document.querySelector("#conversationDiagnostics");
    const downloadTranscriptJson = document.querySelector("#downloadTranscriptJson");
    const downloadTranscriptText = document.querySelector("#downloadTranscriptText");
    const status = document.querySelector("#status");
    const audio = document.querySelector("#audio");
    const interruptAgent = document.querySelector("#interruptAgent");
    const browserSpeak = document.querySelector("#browserSpeak");
    const VOICE_TURN_STATES = Object.freeze({{
      IDLE: "idle",
      LISTENING: "listening",
      AGENT_THINKING: "agent_thinking",
      AGENT_SPEAKING: "agent_speaking",
      PAUSED: "paused"
    }});
    const TERMINAL_CALL_CONTROLS = new Set(["end-call", "hang-up", "schedule-and-end", "close-and-log-sale-ready", "transfer-or-escalate"]);
    const RESTART_AFTER_AGENT_OUTPUT_MS = metadata.turn_taking.restart_after_agent_output_ms;
    const TURN_TAKING_POLICY = metadata.browser_asr.turn_taking_policy;
    const FINAL_TRANSCRIPT_SUBMIT_DELAY_MS = metadata.browser_asr.acceptance_policy.final_transcript_submit_delay_ms;
    const REQUIRE_FINAL_RESULT_FOR_AUTO_SUBMIT = TURN_TAKING_POLICY.requires_final_result_for_auto_submit;
    const SUBMIT_ON_INTERIM_RESULTS = TURN_TAKING_POLICY.submit_on_interim_results;
    const MIN_LISTENING_WINDOW_BEFORE_SUBMIT_MS = TURN_TAKING_POLICY.min_listening_window_before_submit_ms;
    const AGENT_PLAYBACK_VOLUME = metadata.playback.agent_audio_volume;
    const BROWSER_FALLBACK_VOICE_VOLUME = metadata.playback.browser_fallback_voice_volume;
    const BROWSER_FALLBACK_VOICE_RATE = metadata.playback.browser_fallback_voice_rate;
    let recognition = null;
    let latestResponse = "";
    let latestSpeechText = "";
    let autoConversation = false;
    let recognitionActive = false;
    let turnInFlight = false;
    let voiceTurnState = VOICE_TURN_STATES.IDLE;
    let sessionStarted = false;
    let restartTimer = null;
    let finalSubmitTimer = null;
    let lastSubmittedTranscript = "";
    let lastTranscriptConfidence = null;
    let lastResultHadFinal = false;
    let listeningStartedAt = 0;
    let stoppingRecognitionForAgentTurn = false;
    let callEnded = false;
    let fallbackVoice = null;
    const conversationTranscript = [];
    const sessionId = (window.crypto && window.crypto.randomUUID) ? window.crypto.randomUUID() : String(Date.now());

    function setStatus(text) {{ status.textContent = text; }}

    function isTerminalCallControl(callControl) {{
      return TERMINAL_CALL_CONTROLS.has(String(callControl || ""));
    }}

    function setVoiceTurnState(nextState, message=null) {{
      voiceTurnState = nextState;
      if (message) setStatus(message);
    }}

    function isWeakAutoTranscript(text) {{
      const normalized = text.toLowerCase().replace(/[^a-z0-9$]+/g, " ").trim();
      if (!normalized) return true;
      const words = normalized.split(/\\s+/).filter(Boolean);
      const weakEndings = new Set(["a", "an", "the", "about", "of", "to", "for", "with", "and", "or", "but"]);
      return words.length <= 8 && weakEndings.has(words[words.length - 1]);
    }}

    function shouldAcceptAutoTranscript(text, confidence, hasFinalResult=lastResultHadFinal) {{
      if (!text.trim()) return {{ accepted: false, reason: "empty_transcript" }};
      if (voiceTurnState === VOICE_TURN_STATES.AGENT_SPEAKING || voiceTurnState === VOICE_TURN_STATES.AGENT_THINKING) {{
        return {{ accepted: false, reason: "agent_not_listening" }};
      }}
      if (turnInFlight) return {{ accepted: false, reason: "turn_in_flight" }};
      if (!hasFinalResult && REQUIRE_FINAL_RESULT_FOR_AUTO_SUBMIT) {{
        return {{ accepted: false, reason: "wait_for_final_result" }};
      }}
      const listeningElapsedMs = listeningStartedAt ? Date.now() - listeningStartedAt : 0;
      if (listeningElapsedMs < MIN_LISTENING_WINDOW_BEFORE_SUBMIT_MS) {{
        return {{ accepted: false, reason: "minimum_listening_window", retry_after_ms: MIN_LISTENING_WINDOW_BEFORE_SUBMIT_MS - listeningElapsedMs }};
      }}
      if (isWeakAutoTranscript(text)) return {{ accepted: false, reason: "fragment" }};
      if (typeof confidence === "number" && confidence < metadata.browser_asr.acceptance_policy.low_confidence_threshold) {{
        return {{ accepted: false, reason: "low_confidence" }};
      }}
      return {{ accepted: true, reason: "accepted" }};
    }}

    function clearFinalSubmitTimer() {{
      if (finalSubmitTimer) {{
        window.clearTimeout(finalSubmitTimer);
        finalSubmitTimer = null;
      }}
    }}

    function stopRecognitionForAgentTurn() {{
      if (restartTimer) {{
        window.clearTimeout(restartTimer);
        restartTimer = null;
      }}
      clearFinalSubmitTimer();
      if (recognition && recognitionActive) {{
        stoppingRecognitionForAgentTurn = true;
        try {{ recognition.stop(); }} catch (error) {{ /* browser may already be stopping */ }}
      }}
    }}

    function scheduleAutoSubmit() {{
      clearFinalSubmitTimer();
      const listeningElapsedMs = listeningStartedAt ? Date.now() - listeningStartedAt : 0;
      const minimumWindowDelayMs = Math.max(0, MIN_LISTENING_WINDOW_BEFORE_SUBMIT_MS - listeningElapsedMs);
      const submitDelayMs = Math.max(FINAL_TRANSCRIPT_SUBMIT_DELAY_MS, minimumWindowDelayMs);
      finalSubmitTimer = window.setTimeout(() => {{
        finalSubmitTimer = null;
        if (!autoConversation || turnInFlight || callEnded) return;
        const text = transcript.value.trim();
        const acceptance = shouldAcceptAutoTranscript(text, lastTranscriptConfidence, lastResultHadFinal);
        if (text && acceptance.accepted && text !== lastSubmittedTranscript) {{
          submitTurn(true);
          return;
        }}
        if (autoConversation && !recognitionActive) {{
          restartTimer = window.setTimeout(startRecognition, 250);
        }}
      }}, submitDelayMs);
    }}

    function campaignLanguage(campaignId) {{
      const option = metadata.campaign_options.find(item => item.campaign_id === campaignId);
      return option ? option.language : "en";
    }}

    function selectFallbackVoice() {{
      if (fallbackVoice) return fallbackVoice;
      const voices = window.speechSynthesis ? window.speechSynthesis.getVoices() : [];
      const desiredLang = language.value.toLowerCase().slice(0, 2);
      fallbackVoice = voices.find(voice => voice.lang && voice.lang.toLowerCase().startsWith(desiredLang))
        || voices.find(voice => voice.lang && voice.lang.toLowerCase().startsWith("en"))
        || voices[0]
        || null;
      return fallbackVoice;
    }}

    if (window.speechSynthesis) {{
      window.speechSynthesis.onvoiceschanged = () => {{
        if (!fallbackVoice) selectFallbackVoice();
      }};
    }}

    function syncLanguageToCampaign() {{
      language.value = campaignLanguage(campaign.value).startsWith("de") ? "de-DE" : "en-US";
    }}

    metadata.campaign_options.forEach(item => {{
      const option = document.createElement("option");
      option.value = item.campaign_id;
      option.textContent = `${{item.campaign_id}} (${{item.language}})`;
      if (item.campaign_id === metadata.default_campaign_id) option.selected = true;
      campaign.appendChild(option);
    }});
    syncLanguageToCampaign();
    campaign.addEventListener("change", syncLanguageToCampaign);

    function startRecognition() {{
      if (!autoConversation) return;
      if (!consent.checked) {{ setStatus("Consent is required before microphone use."); return; }}
      if (!SpeechRecognition) {{ setStatus("Speech recognition is not available in this browser."); return; }}
      if (recognitionActive || turnInFlight) return;
      if (voiceTurnState === VOICE_TURN_STATES.AGENT_THINKING || voiceTurnState === VOICE_TURN_STATES.AGENT_SPEAKING) return;
      recognition = new SpeechRecognition();
      recognition.lang = language.value;
      recognition.interimResults = true;
      recognition.continuous = true;
      recognition.onstart = () => {{
        recognitionActive = true;
        stoppingRecognitionForAgentTurn = false;
        listeningStartedAt = Date.now();
        lastResultHadFinal = false;
        clearFinalSubmitTimer();
        setVoiceTurnState(VOICE_TURN_STATES.LISTENING, "Listening...");
      }};
      recognition.onerror = event => setStatus(`ASR error: ${{event.error}}`);
      recognition.onend = () => {{
        recognitionActive = false;
        if (stoppingRecognitionForAgentTurn) {{
          stoppingRecognitionForAgentTurn = false;
          return;
        }}
        const text = transcript.value.trim();
        const acceptance = shouldAcceptAutoTranscript(text, lastTranscriptConfidence, lastResultHadFinal);
        if (autoConversation && text && acceptance.reason === "minimum_listening_window" && lastResultHadFinal) {{
          setVoiceTurnState(VOICE_TURN_STATES.LISTENING, "Heard a final phrase. Waiting for the pause window.");
          scheduleAutoSubmit();
          return;
        }}
        if (autoConversation && text && !acceptance.accepted) {{
          setVoiceTurnState(VOICE_TURN_STATES.LISTENING, `Transcript rejected (${{acceptance.reason}}). Please repeat the question.`);
          transcript.value = "";
          lastSubmittedTranscript = "";
          lastResultHadFinal = false;
          restartTimer = window.setTimeout(startRecognition, 500);
          return;
        }}
        if (autoConversation && text && text !== lastSubmittedTranscript) {{
          setVoiceTurnState(VOICE_TURN_STATES.LISTENING, "Heard a final phrase. Waiting briefly before agent response...");
          scheduleAutoSubmit();
        }} else if (autoConversation) {{
          setVoiceTurnState(VOICE_TURN_STATES.LISTENING, "Listening ended without a new transcript. Starting again...");
          restartTimer = window.setTimeout(startRecognition, 500);
        }} else {{
          setVoiceTurnState(VOICE_TURN_STATES.PAUSED, "Stopped. Review transcript, then send.");
        }}
      }};
      recognition.onresult = event => {{
        let text = "";
        let confidence = null;
        let sawFinalResult = false;
        for (let i = 0; i < event.results.length; i += 1) {{
          const result = event.results[i];
          text += result[0].transcript;
          if (result.isFinal && typeof result[0].confidence === "number") {{
            confidence = confidence === null ? result[0].confidence : Math.max(confidence, result[0].confidence);
          }}
          if (result.isFinal) {{
            sawFinalResult = true;
          }}
        }}
        lastTranscriptConfidence = confidence;
        lastResultHadFinal = sawFinalResult;
        transcript.value = text.trim();
        if (autoConversation && text.trim()) {{
          if (!sawFinalResult && REQUIRE_FINAL_RESULT_FOR_AUTO_SUBMIT) {{
            clearFinalSubmitTimer();
            setVoiceTurnState(VOICE_TURN_STATES.LISTENING, "Listening... waiting for you to finish.");
            return;
          }}
          if (!sawFinalResult && !SUBMIT_ON_INTERIM_RESULTS) {{
            clearFinalSubmitTimer();
            setVoiceTurnState(VOICE_TURN_STATES.LISTENING, "Listening... still hearing your sentence.");
            return;
          }}
          const acceptance = shouldAcceptAutoTranscript(text, lastTranscriptConfidence, sawFinalResult || SUBMIT_ON_INTERIM_RESULTS);
          if (acceptance.accepted && text.trim() !== lastSubmittedTranscript) {{
            setVoiceTurnState(VOICE_TURN_STATES.LISTENING, "Listening... waiting for a pause.");
            scheduleAutoSubmit();
          }} else if (acceptance.reason === "minimum_listening_window") {{
            setVoiceTurnState(VOICE_TURN_STATES.LISTENING, "Listening... waiting for the pause window.");
            scheduleAutoSubmit();
          }}
        }}
      }};
      recognition.start();
    }}

    listen.addEventListener("click", () => {{
      if (callEnded) {{
        setVoiceTurnState(VOICE_TURN_STATES.PAUSED, "Conversation ended. Listening will not restart.");
        return;
      }}
      if (!consent.checked) {{ setStatus("Consent is required before microphone use."); return; }}
      autoConversation = true;
      if (!sessionStarted) {{
        startAgentOpening();
        return;
      }}
      startRecognition();
    }});

    stop.addEventListener("click", () => {{
      autoConversation = false;
      if (restartTimer) {{
        window.clearTimeout(restartTimer);
        restartTimer = null;
      }}
      if (recognition) recognition.stop();
      if (!audio.paused) audio.pause();
      window.speechSynthesis.cancel();
      setVoiceTurnState(VOICE_TURN_STATES.PAUSED, "Conversation stopped.");
    }});

    function interruptAgentPlayback() {{
      if (callEnded) {{
        setVoiceTurnState(VOICE_TURN_STATES.PAUSED, "Conversation ended. Listening will not restart.");
        return;
      }}
      if (!consent.checked) {{
        setStatus("Consent is required before microphone use.");
        return;
      }}
      if (restartTimer) {{
        window.clearTimeout(restartTimer);
        restartTimer = null;
      }}
      clearFinalSubmitTimer();
      autoConversation = true;
      if (!audio.paused) {{
        audio.pause();
        try {{ audio.currentTime = 0; }} catch (error) {{ /* some browsers block seek on unloaded audio */ }}
      }}
      window.speechSynthesis.cancel();
      transcript.value = "";
      lastResultHadFinal = false;
      lastSubmittedTranscript = "";
      setVoiceTurnState(VOICE_TURN_STATES.LISTENING, "Agent interrupted. Listening...");
      window.setTimeout(startRecognition, 50);
    }}

    interruptAgent.addEventListener("click", interruptAgentPlayback);
    document.addEventListener("keydown", event => {{
      if (event.key !== "Escape" || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
      if (voiceTurnState !== VOICE_TURN_STATES.AGENT_SPEAKING) return;
      event.preventDefault();
      interruptAgentPlayback();
    }});

    function startAgentOpening() {{
      if (turnInFlight) return;
      sessionStarted = true;
      lastTranscriptConfidence = null;
      submitTurn(true, AGENT_OPEN_TRANSCRIPT, "agent-open");
    }}

    function providerBoundaryForTranscript(payload) {{
      return {{
        provider_agent_used: payload.provider_agent_used,
        durable_provider_agent_created: payload.durable_provider_agent_created,
        elevenlabs_call_made: payload.summary.tts_provider_calls_made,
        audio_file_created: payload.summary.tts_audio_file_created,
        fallback_reason: payload.summary.tts_fallback_reason,
        voice_cloning_used: payload.voice_cloning_used,
        opens_prod_102: payload.opens_prod_102
      }};
    }}

    function appendConversationTranscriptTurn(inputText, inputType, payload) {{
      const visibleTranscript = inputText === AGENT_OPEN_TRANSCRIPT ? "(agent opening)" : inputText;
      conversationTranscript.push({{
        turn_index: payload.session_turn_index,
        input_type: inputType,
        customer_transcript: visibleTranscript,
        agent_response: payload.summary.final_response,
        call_control: payload.summary.call_control,
        demo_conversation_memory: payload.demo_conversation_memory || {{}},
        demo_conversation_stability_guard: payload.demo_conversation_stability_guard || {{}},
        async_enrichment_boundary: payload.dialogue_reasoner_async_enrichment || {{}},
        provider_boundary: providerBoundaryForTranscript(payload),
        latency: payload.latency || {{}}
      }});
      renderConversationTranscript();
    }}

    function renderConversationTranscriptText() {{
      if (!conversationTranscript.length) return "No turns yet.";
      return conversationTranscript.map(turn => {{
        const lines = [
          `#${{turn.turn_index}} ${{turn.input_type}}`,
          `Buyer: ${{turn.customer_transcript}}`,
          `Agent: ${{turn.agent_response}}`,
          `Call control: ${{turn.call_control}}`
        ];
        return lines.join("\\n");
      }}).join("\\n\\n");
    }}

    function renderConversationDiagnosticsText() {{
      if (!conversationTranscript.length) return "No diagnostics yet.";
      return conversationTranscript.map(turn => {{
        const diagnostics = {{
          turn_index: turn.turn_index,
          memory: turn.demo_conversation_memory,
          stability_guard: turn.demo_conversation_stability_guard,
          provider_boundary: turn.provider_boundary,
          latency: turn.latency
        }};
        return JSON.stringify(diagnostics, null, 2);
      }}).join("\\n\\n");
    }}

    function renderConversationTranscript() {{
      conversationTranscriptBox.textContent = renderConversationTranscriptText();
      conversationDiagnosticsBox.textContent = renderConversationDiagnosticsText();
    }}

    function transcriptDownloadPayload() {{
      return {{
        live_demo_id: metadata.live_demo_id,
        session_id: sessionId,
        campaign_id: campaign.value || metadata.default_campaign_id,
        generated_at: new Date().toISOString(),
        audio_stored: false,
        customer_audio_uploaded_to_python_server: false,
        turns: conversationTranscript
      }};
    }}

    function downloadTranscript(format) {{
      const isJson = format === "json";
      const body = isJson
        ? JSON.stringify(transcriptDownloadPayload(), null, 2)
        : renderConversationTranscriptText();
      const blob = new Blob([body], {{ type: isJson ? "application/json" : "text/plain" }});
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = `${{metadata.live_demo_id || "live-demo"}}-${{sessionId}}-transcript.${{isJson ? "json" : "txt"}}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(link.href), 1000);
    }}

    async function submitTurn(fromAutoConversation=false, transcriptOverride=null, inputTypeOverride="speech-final") {{
      if (callEnded) {{
        setVoiceTurnState(VOICE_TURN_STATES.PAUSED, "Conversation ended. Listening will not restart.");
        return;
      }}
      const text = (transcriptOverride === null ? transcript.value : transcriptOverride).trim();
      if (!text) {{ setStatus("Transcript is empty."); return; }}
      if (turnInFlight) return;
      stopRecognitionForAgentTurn();
      const acceptedVoiceTurnState = voiceTurnState;
      lastSubmittedTranscript = text;
      turnInFlight = true;
      send.disabled = true;
      setVoiceTurnState(VOICE_TURN_STATES.AGENT_THINKING, "Running local agent...");
      try {{
        const result = await fetch("/turn", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{
            transcript: text,
            campaign_id: campaign.value || metadata.default_campaign_id,
            stage: metadata.default_stage,
            input_type: inputTypeOverride,
            session_id: sessionId,
            asr_confidence: transcriptOverride === null ? lastTranscriptConfidence : null,
            voice_turn_state: acceptedVoiceTurnState
          }})
        }});
        const payload = await result.json();
        if (!result.ok) throw new Error(payload.error || `HTTP ${{result.status}}`);
        sessionStarted = true;
        latestResponse = payload.summary.final_response;
        latestSpeechText = payload.summary.browser_fallback_speech_text || payload.summary.tts_input_text || payload.packet?.tts_delivery?.tts_input_text || latestResponse;
        callEnded = isTerminalCallControl(payload.summary.call_control);
        responseBox.textContent = latestResponse;
        decision.textContent = JSON.stringify({{
          sales_difficulty: payload.summary.sales_difficulty,
          detected_emotion: payload.summary.detected_emotion,
          selected_strategy: payload.summary.selected_strategy,
          next_action: payload.summary.next_action,
          call_control: payload.summary.call_control,
          tts_input_source: payload.summary.tts_input_source,
          retrieval_status: payload.summary.retrieval_status,
          retrieval_used_in_runtime: payload.summary.retrieval_used_in_runtime,
          composer_hooks_status: payload.summary.composer_hooks_status,
          composer_hooks_applied: payload.summary.composer_hooks_applied
        }}, null, 2);
        boundary.textContent = JSON.stringify({{
          provider_agent_used: payload.provider_agent_used,
          elevenlabs_call_made: payload.summary.tts_provider_calls_made,
          audio_file_created: payload.summary.tts_audio_file_created,
          fallback_reason: payload.summary.tts_fallback_reason,
          fallback_speaks_provider_tts_input: latestSpeechText !== latestResponse,
          retrieved_item_ids: payload.summary.retrieved_item_ids,
          voice_cloning_used: payload.voice_cloning_used,
          runtime_behavior_changed: payload.runtime_behavior_changed,
          opens_prod_102: payload.opens_prod_102
        }}, null, 2);
        packet.textContent = JSON.stringify(payload, null, 2);
        appendConversationTranscriptTurn(text, inputTypeOverride, payload);
        transcript.value = "";
        if (payload.audio_url) {{
          audio.src = payload.audio_url;
          audio.volume = AGENT_PLAYBACK_VOLUME;
          setVoiceTurnState(VOICE_TURN_STATES.AGENT_SPEAKING, "Agent speaking...");
          await audio.play();
        }} else {{
          audio.removeAttribute("src");
          if (fromAutoConversation) {{
            if (metadata.tts.live_tts_enabled && payload.summary.tts_provider_calls_made) {{
              autoConversation = false;
              setVoiceTurnState(VOICE_TURN_STATES.PAUSED, `ElevenLabs audio unavailable (${{payload.summary.tts_fallback_reason || "unknown"}}). Browser fallback is manual to avoid switching voices mid-call.`);
            }} else {{
              setVoiceTurnState(VOICE_TURN_STATES.AGENT_THINKING, "No ElevenLabs audio file. Using fallback voice.");
              playBrowserFallback();
            }}
          }} else {{
            setVoiceTurnState(VOICE_TURN_STATES.IDLE, "No ElevenLabs audio file. Use fallback voice or check env gates.");
          }}
        }}
      }} catch (error) {{
        setVoiceTurnState(VOICE_TURN_STATES.PAUSED, `Turn failed: ${{error.message}}`);
      }} finally {{
        send.disabled = false;
        turnInFlight = false;
      }}
    }}

    send.addEventListener("click", () => {{
      autoConversation = false;
      submitTurn(false);
    }});

    function restartAfterAgentSpeech() {{
      if (callEnded) {{
        autoConversation = false;
        setVoiceTurnState(VOICE_TURN_STATES.PAUSED, "Conversation ended. Listening will not restart.");
        return;
      }}
      if (autoConversation) {{
        setVoiceTurnState(VOICE_TURN_STATES.LISTENING, "Agent finished. Listening will restart.");
        restartTimer = window.setTimeout(startRecognition, RESTART_AFTER_AGENT_OUTPUT_MS);
      }} else {{
        setVoiceTurnState(VOICE_TURN_STATES.IDLE, "Agent finished.");
      }}
    }}

    const restartListenAfterAgentOutput = restartAfterAgentSpeech;
    audio.addEventListener("play", () => setVoiceTurnState(VOICE_TURN_STATES.AGENT_SPEAKING, "Agent speaking..."));
    audio.addEventListener("ended", restartListenAfterAgentOutput);
    audio.addEventListener("error", restartListenAfterAgentOutput);

    function playBrowserFallback() {{
      if (!latestResponse) latestResponse = responseBox.textContent.trim();
      if (!latestSpeechText) latestSpeechText = latestResponse;
      stopRecognitionForAgentTurn();
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(latestSpeechText);
      utterance.lang = language.value;
      fallbackVoice = selectFallbackVoice();
      if (fallbackVoice) utterance.voice = fallbackVoice;
      utterance.rate = BROWSER_FALLBACK_VOICE_RATE;
      utterance.volume = BROWSER_FALLBACK_VOICE_VOLUME;
      utterance.onstart = () => setVoiceTurnState(VOICE_TURN_STATES.AGENT_SPEAKING, "Browser fallback voice speaking...");
      utterance.onend = restartListenAfterAgentOutput;
      utterance.onerror = restartListenAfterAgentOutput;
      window.speechSynthesis.speak(utterance);
    }}

    browserSpeak.addEventListener("click", () => {{
      autoConversation = false;
      playBrowserFallback();
    }});
    downloadTranscriptJson.addEventListener("click", () => downloadTranscript("json"));
    downloadTranscriptText.addEventListener("click", () => downloadTranscript("txt"));
  </script>
</body>
</html>
"""


def render_report(turn: dict) -> str:
    summary = turn["summary"]
    lines = [
        "# LIVE-DEMO-001 Agent Voice Call Turn",
        "",
        "This private turn packet was generated by `scripts/run_live_demo_001_agent_voice_call.py`.",
        "",
        f"- Mode: `{turn['mode']}`",
        f"- Sales difficulty: `{summary['sales_difficulty']}`",
        f"- Strategy: `{summary['selected_strategy']}`",
        f"- Call control: `{summary['call_control']}`",
        f"- Provider agent used: `{str(turn['provider_agent_used']).lower()}`",
        f"- TTS provider calls made: `{str(summary['tts_provider_calls_made']).lower()}`",
        f"- TTS audio file created: `{str(summary['tts_audio_file_created']).lower()}`",
        f"- TTS fallback reason: `{summary['tts_fallback_reason']}`",
        f"- Voice cloning used: `{str(turn['voice_cloning_used']).lower()}`",
        f"- Runtime behavior changed: `{str(turn['runtime_behavior_changed']).lower()}`",
        f"- Opens PROD-102: `{str(turn['opens_prod_102']).lower()}`",
        "",
        "## Response",
        "",
        summary["final_response"],
        "",
    ]
    return "\n".join(lines)


def private_turn_paths(private_out: Path) -> tuple[Path, Path]:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    stem = f"LIVE-DEMO-001-turn-{stamp}"
    return private_out / f"{stem}.json", private_out / f"{stem}.md"


def live_demo_retrieval_kwargs() -> dict:
    enabled = DEFAULT_RETRIEVAL_REGISTRY.exists()
    return {
        "retrieval_enabled": enabled,
        "retrieval_registry_path": DEFAULT_RETRIEVAL_REGISTRY if enabled else None,
        "composer_hooks_enabled": enabled,
    }


def persist_private_turn(private_out: Path, turn: dict) -> None:
    json_path, report_path = private_turn_paths(private_out)
    turn["private_artifacts"] = {
        "json": project_relative_string(json_path),
        "report": project_relative_string(report_path),
    }
    write_json(json_path, turn)
    write_text(report_path, render_report(turn))


def safe_audio_path(requested: str, private_out: Path) -> Path:
    candidate = (ROOT / requested).resolve()
    allowed = private_out.resolve()
    if not str(candidate).startswith(str(allowed)):
        raise ValueError("audio path is outside LIVE-DEMO-001 private output")
    if not candidate.is_file():
        raise ValueError("audio file does not exist")
    return candidate


def make_handler(metadata: dict, cases_path: Path, private_out: Path):
    sessions: dict[str, dict] = {}

    class LiveDemoHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args) -> None:
            return

        def send_json(self, payload: dict, status: int = 200) -> None:
            body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/":
                body = render_html(metadata).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if parsed.path == "/metadata":
                self.send_json(metadata)
                return
            if parsed.path == "/audio":
                try:
                    requested = parse_qs(parsed.query).get("path", [""])[0]
                    audio_path = safe_audio_path(requested, private_out)
                    body = audio_path.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", mimetypes.guess_type(str(audio_path))[0] or "application/octet-stream")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                except Exception as exc:
                    self.send_json({"error": str(exc)}, status=404)
                return
            self.send_json({"error": "not found"}, status=404)

        def do_POST(self) -> None:
            if urlparse(self.path).path != "/turn":
                self.send_json({"error": "not found"}, status=404)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
                transcript = str(payload.get("transcript") or "").strip()
                if not transcript:
                    self.send_json({"error": "transcript is required"}, status=400)
                    return
                session_id = str(payload.get("session_id") or "default-session")
                session_state = sessions.setdefault(session_id, {"turns": []})
                turn = build_turn_packet(
                    transcript=transcript,
                    campaign_id=str(payload.get("campaign_id") or metadata["default_campaign_id"]),
                    stage=str(payload.get("stage") or metadata["default_stage"]),
                    input_type=str(payload.get("input_type") or "speech-final"),
                    silence_count=int(payload.get("silence_count") or 0),
                    cases_path=cases_path,
                    private_out=private_out,
                    live_tts=metadata["tts"]["live_tts_enabled"],
                    force_key_missing=metadata["tts"]["force_key_missing"],
                    timeout_seconds=float(metadata["tts"]["timeout_seconds"]),
                    session_id=session_id,
                    session_state=session_state,
                    asr_confidence=payload.get("asr_confidence"),
                    voice_turn_state=payload.get("voice_turn_state") or payload.get("turn_state"),
                )
                persist_private_turn(private_out, turn)
                session_state["turns"].append(
                    {
                        "transcript": transcript,
                        "summary": turn.get("summary", {}),
                        "continuity": turn.get("demo_session_continuity", {}),
                        "conversation_memory": turn.get("demo_conversation_memory", {}),
                    }
                )
                self.send_json(turn)
            except Exception as exc:
                self.send_json({"error": str(exc)}, status=500)

    return LiveDemoHandler


def serve(metadata: dict, cases_path: Path, private_out: Path) -> None:
    server = ThreadingHTTPServer(
        (metadata["local_server"]["host"], metadata["local_server"]["port"]),
        make_handler(metadata, cases_path, private_out),
    )
    print(metadata["local_server"]["url"])
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run LIVE-DEMO-001: browser mic -> repo agent -> ElevenLabs voice.")
    parser.add_argument("--campaign", default=DEFAULT_CAMPAIGN_ID)
    parser.add_argument("--stage", default=DEFAULT_STAGE)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--cases", default=str(DEFAULT_CASES_PATH))
    parser.add_argument("--private-out", default=str(DEFAULT_PRIVATE_OUT))
    parser.add_argument("--timeout-seconds", type=float, default=8.0)
    parser.add_argument("--live-tts", action="store_true", help="Allow ElevenLabs TTS provider calls.")
    parser.add_argument("--force-key-missing", action="store_true", help="Validate missing-key fallback without reading provider env vars.")
    parser.add_argument("--consent-confirmed", action="store_true", help="Confirm Tarik-approved local live demo boundary.")
    parser.add_argument(
        "--elevenlabs-env-file",
        default=str(DEFAULT_ELEVENLABS_ENV_FILE),
        help="Ignored local env file for ElevenLabs live TTS. Defaults to runtime/config/local/elevenlabs.env.",
    )
    parser.add_argument("--export-html")
    parser.add_argument("--export-metadata")
    parser.add_argument("--decision-transcript")
    parser.add_argument("--decision-out")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.timeout_seconds <= 0 or args.timeout_seconds > 10:
        raise SystemExit("--timeout-seconds must be greater than 0 and no more than 10.")
    if args.live_tts and not args.consent_confirmed:
        raise SystemExit("--consent-confirmed is required with --live-tts.")

    cases_path = resolve_project_path(args.cases)
    private_out = resolve_project_path(args.private_out)
    if cases_path is None or private_out is None:
        raise SystemExit("Cases and private output paths are required.")
    env_file = resolve_project_path(args.elevenlabs_env_file)
    args.live_tts_env_file_status = load_live_tts_env_file(env_file)
    args.live_tts_preflight = live_tts_preflight(args.campaign, cases_path, args.force_key_missing)
    if args.live_tts and not args.force_key_missing:
        require_live_tts_ready(args.live_tts_preflight, args.live_tts_env_file_status)
    metadata = build_metadata(args, cases_path, private_out)

    if args.decision_transcript:
        turn = build_turn_packet(
            transcript=args.decision_transcript,
            campaign_id=args.campaign,
            stage=args.stage,
            input_type="speech-final",
            silence_count=0,
            cases_path=cases_path,
            private_out=private_out,
            live_tts=args.live_tts,
            force_key_missing=args.force_key_missing,
            timeout_seconds=args.timeout_seconds,
        )
        decision_out = resolve_project_path(args.decision_out)
        if decision_out is not None:
            write_json(decision_out, turn)
        print(json.dumps(turn, indent=2, ensure_ascii=False))
        return

    exported = False
    export_html = resolve_project_path(args.export_html)
    if export_html is not None:
        write_text(export_html, render_html(metadata))
        exported = True
    export_metadata = resolve_project_path(args.export_metadata)
    if export_metadata is not None:
        write_json(export_metadata, metadata)
        exported = True
    if exported:
        print(json.dumps(metadata, indent=2, ensure_ascii=False))
        return

    serve(metadata, cases_path, private_out)


if __name__ == "__main__":
    main()
