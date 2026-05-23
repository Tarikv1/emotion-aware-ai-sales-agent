#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

if str(ROOT := Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_live_demo_001_agent_voice_call import (  # noqa: E402
    DEFAULT_CASES_PATH,
    build_turn_packet,
)

SCRIPT_PATH = ROOT / "scripts" / "run_live_demo_001_agent_voice_call.py"
PROFILE_PATH = ROOT / "research" / "experiments" / "cases" / "live-demo-001-fictional-b2b-sales-campaign.json"
TMP_DIR = ROOT / ".tmp" / "LIVE-DEMO-001"
HTML_OUT = TMP_DIR / "LIVE-DEMO-001.html"
METADATA_OUT = TMP_DIR / "LIVE-DEMO-001-metadata.json"
DRY_OUT = TMP_DIR / "LIVE-DEMO-001-dry-turn.json"
FORCED_OUT = TMP_DIR / "LIVE-DEMO-001-forced-missing-key-turn.json"
ENV_METADATA_OUT = TMP_DIR / "LIVE-DEMO-001-env-metadata.json"
LIVE_TTS_ENV_FILE = TMP_DIR / "elevenlabs.env"
MISSING_LIVE_TTS_ENV_FILE = TMP_DIR / "missing-default-elevenlabs.env"
TRANSCRIPT = "I am not sure this makes sense for my apartment right now."
REQUIRED_SOURCE_URLS = {
    "https://info.chilipiper.com/lead-routing-software",
    "https://calendly.com/features/routing",
    "https://www.hubspot.com/products/lead-scoring",
    "https://www.leandata.com/platform/speed-to-lead/",
}

SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|sk_[A-Za-z0-9_-]{20,}|ELEVENLABS_API_KEY\s*=\s*[^\s]+|xi-api-key\s*[:=]\s*[A-Za-z0-9]|Authorization:\s*Bearer\s+[A-Za-z0-9])"
)


def safe_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("ELEVENLABS_API_KEY", None)
    env.pop("ELEVENLABS_VOICE_ID", None)
    env.pop("ELEVENLABS_VOICE_ID_EN", None)
    return env


def run_demo(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        cwd=ROOT,
        env=safe_env(),
        text=True,
        capture_output=True,
        check=True,
    )


def run_demo_raw(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        cwd=ROOT,
        env=safe_env(),
        text=True,
        capture_output=True,
        check=False,
    )


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_no_secret_patterns(text: str) -> None:
    match = SECRET_PATTERN.search(text)
    if match is not None:
        raise AssertionError(f"Potential secret-like token found: {match.group(0)!r}")


def assert_no_tts_word_split_breaks(text: str, context: str) -> None:
    pattern = re.compile(
        r"\b(owner|callback|handoff|lead|reminder)\s*<break\s+time=\"[^\"]+\"\s*/?>\s*s\b",
        re.IGNORECASE,
    )
    match = pattern.search(text)
    if match is not None:
        raise AssertionError(f"{context} split a plural word with a TTS break tag: {match.group(0)!r}")


def response_reopens_focus_menu(response: str) -> bool:
    lowered = response.lower()
    return (
        "main question about price, fit, timing" in lowered
        or "bigger concern the monthly price" in lowered
        or "main concern whether this is relevant for your situation, the price, or the timing" in lowered
    )


DEMO_STYLE_BLOCKLIST = [
    "that makes sense",
    "bigger concern",
    "main question about price, fit, timing",
    "focus only on price",
    "stay on price",
    "we will stay on price",
    "let's keep",
    "lets keep",
    "keep it on price",
    "right, we will",
    "good, then",
    "avoid repeating",
    "same question",
    "keep the next step narrow",
    "i will not reopen",
    "specific part you want",
    "price-and-scope",
    "approved pricing facts",
    "still the blocker",
    "switch to a written",
    "written price",
]


def assert_sales_opening_response(response: str) -> None:
    lowered = response.lower()
    assert_condition(
        any(fragment in lowered for fragment in {"do you have a minute", "is now a bad time", "quick question"}),
        f"Opening should behave like a sales opener with permission/time check: {response}",
    )
    assert_condition(
        "calling from" in lowered and "team behind" in lowered,
        f"Opening should make the seller company and product relationship unambiguous: {response}",
    )
    assert_condition(
        any(fragment in response for fragment in {"Northstar Workflow Labs", "RouteSignal"}),
        f"Opening should name the fictional company or product instead of acting like generic chat: {response}",
    )
    assert_condition(
        any(fragment in lowered for fragment in {"missed callback", "missed follow-up", "handoff", "routing"}),
        f"Opening should state the sales problem being checked: {response}",
    )
    assert_condition("?" in response, f"Opening should ask a qualifying sales question: {response}")
    assert_condition(
        "price, fit" not in lowered and "what do you want to check first" not in lowered,
        f"Opening should not start with a topic menu: {response}",
    )


def assert_live_demo_response_style(response: str, context: str) -> None:
    lowered = response.lower()
    for fragment in DEMO_STYLE_BLOCKLIST:
        assert_condition(fragment not in lowered, f"{context} response used blocked live-demo wording: {response}")
    words = re.findall(r"[A-Za-z0-9$]+(?:'[A-Za-z0-9]+)?", response)
    assert_condition(len(words) <= 44, f"{context} response is too long for live demo: {response}")
    sentences = [part.strip() for part in re.split(r"[.!?]+", response) if part.strip()]
    for sentence in sentences:
        sentence_words = re.findall(r"[A-Za-z0-9$]+(?:'[A-Za-z0-9]+)?", sentence)
        assert_condition(len(sentence_words) <= 22, f"{context} sentence is too long: {response}")


def assert_browser_fallback_text_clean(response: str, context: str) -> None:
    assert_condition("<" not in response and ">" not in response, f"{context} fallback leaked provider markup: {response}")
    assert_condition(
        re.search(r"\s+[,.;:!?]", response) is None,
        f"{context} fallback has spoken punctuation spacing: {response}",
    )


def assert_opening_identity_fallback_clean(response: str) -> None:
    assert_condition(
        re.search(
            r"(?:northstar workflow labs|routesignal crm)[,.]?\s+(?:um|uh|well|so|right|okay|ok)[,.]?\s+do you have a minute",
            response,
            re.IGNORECASE,
        )
        is None,
        f"Agent opener fallback should not insert a filler between identity and permission check: {response}",
    )


def assert_previous_question_clarified(response: str, context: str) -> None:
    lowered = response.lower()
    assert_condition(
        any(fragment in lowered for fragment in {"i was asking", "i meant", "in plain terms"}),
        f"{context} should explain the previous question plainly: {response}",
    )
    assert_condition(
        any(fragment in lowered for fragment in {"missed callbacks", "handoffs", "owner", "inbound demo"}),
        f"{context} should clarify the actual sales question, not advance a canned line: {response}",
    )
    assert_condition(
        "growth only matters" not in lowered
        and "which part slips most" not in lowered
        and "where does that break" not in lowered,
        f"{context} should not replay qualification sentence-bank wording: {response}",
    )
    assert_condition("?" in response, f"{context} should end with one clearer question: {response}")


def assert_negative_reply_clarified(response: str, context: str) -> None:
    lowered = response.lower()
    assert_condition(
        any(fragment in lowered for fragment in {"do you mean", "are you saying"}),
        f"{context} should clarify what the buyer rejected: {response}",
    )
    assert_condition(
        any(fragment in lowered for fragment in {"not a good time", "none of those gaps", "not an issue"}),
        f"{context} should separate timing rejection from problem rejection: {response}",
    )
    assert_condition(
        any(fragment in lowered for fragment in {"missed callbacks", "handoffs", "gaps"}),
        f"{context} should keep the previous sales question grounded: {response}",
    )
    assert_condition(
        "price, fit, timing" not in lowered
        and "shared inbox leads" not in lowered
        and "owner routing, callback reminders" not in lowered,
        f"{context} should not reopen menus or advance qualification copy: {response}",
    )
    assert_condition("?" in response, f"{context} should ask one clarifying question: {response}")


def assert_callback_workflow_not_scheduling(response: str, context: str) -> None:
    lowered = response.lower()
    assert_condition(
        "what time" not in lowered
        and "call you back" not in lowered
        and "note for the callback" not in lowered
        and "when should" not in lowered,
        f"{context} treated product callbacks as callback scheduling: {response}",
    )
    assert_condition(
        any(
            fragment in lowered
            for fragment in {
                "callback reminder",
                "missed follow-up",
                "inbound demo",
                "demo leads",
                "workflow review",
                "next step",
                "without a next step",
                "owner",
                "reminder",
            }
        ),
        f"{context} should explain callbacks as a workflow/product gap: {response}",
    )
    assert_condition("?" in response, f"{context} should keep guiding the sales conversation: {response}")


def assert_no_generic_focus_menu(response: str, context: str) -> None:
    lowered = response.lower()
    assert_condition(
        "main question about price, fit, timing" not in lowered
        and "price, fit, timing, or exact product details" not in lowered
        and "to make this useful" not in lowered,
        f"{context} fell back to the generic focus menu: {response}",
    )


def assert_call_context_recovered(response: str, context: str) -> None:
    lowered = response.lower()
    assert_no_generic_focus_menu(response, context)
    assert_condition(
        any(fragment in lowered for fragment in {"one question", "i called to check", "not being clear", "quick check", "short means"}),
        f"{context} should answer the call context directly: {response}",
    )
    assert_condition(
        any(fragment in lowered for fragment in {"inbound demo", "demo follow-up", "callback reminder", "handoff", "owner"}),
        f"{context} should stay grounded in the campaign workflow: {response}",
    )
    assert_condition(
        "avoid repeating" not in lowered and "same question" not in lowered and "keep the next step narrow" not in lowered,
        f"{context} leaked internal anti-loop wording: {response}",
    )
    assert_condition("?" in response, f"{context} should ask one concrete next question: {response}")


def assert_caller_identity_recalled(response: str, context: str) -> None:
    lowered = response.lower()
    assert_condition("northstar workflow labs" in lowered, f"{context} should name the caller company: {response}")
    assert_condition("routesignal crm" in lowered, f"{context} should name the product relationship: {response}")
    assert_condition("calling from" in lowered, f"{context} should directly answer where the caller is from: {response}")
    assert_condition(
        "price, fit, timing" not in lowered and "main question" not in lowered and "about the fit" not in lowered,
        f"{context} should not reopen topic menus: {response}",
    )
    assert_no_campaign_depth_regressions(response, context)


def assert_contains_any(response: str, fragments: set[str], context: str) -> None:
    lowered = response.lower()
    assert_condition(
        any(fragment.lower() in lowered for fragment in fragments),
        f"{context} response missed expected campaign substance: {response}",
    )


def strip_leading_voice_filler(response: str) -> str:
    lowered = response.strip().lower()
    return re.sub(r"^(?:um|uh|well|so|right|okay|ok)[,.\s]+", "", lowered)


def assert_no_customer_price_plan_echo(response: str, context: str) -> None:
    lowered = strip_leading_voice_filler(response)
    blocked_prefixes = (
        "$59",
        "59 dollars",
        "fifty nine",
        "growth is",
        "growth plan",
        "the $59",
        "the fifty nine",
        "the growth",
    )
    assert_condition(
        not lowered.startswith(blocked_prefixes),
        f"{context} response echoed the customer's price or plan at the start: {response}",
    )
    blocked_repeated_facts = ("$59", "59/month", "59 dollars", "fifty nine")
    assert_condition(
        not any(fragment in lowered for fragment in blocked_repeated_facts),
        f"{context} response repeated the customer's price fact instead of answering value directly: {response}",
    )


def assert_no_leading_customer_echo(response: str, blocked_prefixes: tuple[str, ...], context: str) -> None:
    lowered = strip_leading_voice_filler(response)
    normalized_blocked = tuple(prefix.lower() for prefix in blocked_prefixes)
    assert_condition(
        not lowered.startswith(normalized_blocked),
        f"{context} response started by echoing the customer's topic instead of answering forward: {response}",
    )


def assert_seller_led_next_move(response: str, context: str) -> None:
    lowered = response.lower()
    assert_condition(
        "?" in response or "if you name the point" in lowered or "useful next step" in lowered,
        f"{context} should end with a buyer-led diagnostic question or direct next-step prompt: {response}",
    )
    assert_condition(
        any(
            fragment in lowered
            for fragment in {
                "where does",
                "where is",
                "which part",
                "which gap",
                "which one",
                "main gap",
                "are missed",
                "frequent enough",
                "should i keep",
                "would a short",
                "what time works",
                "is inbound demo follow-up slipping",
                "is that causing",
                "causing any issue right now",
                "if you name the point",
                "useful next step",
                "concrete workflow gap",
            }
        ),
        f"{context} should guide discovery instead of only giving information: {response}",
    )
    assert_condition(
        not any(fragment in lowered for fragment in {"book a demo", "sign up", "buy", "commit today"}),
        f"{context} should guide without hard-close pressure: {response}",
    )


def assert_sales_context_depth(response: str, context: str) -> None:
    lowered = response.lower()
    blocked_generic = {
        "the narrow check",
        "the sales case is simple",
        "feature-wise",
        "that workflow gap",
    }
    for fragment in blocked_generic:
        assert_condition(fragment not in lowered, f"{context} used thin generic sales wording: {response}")
    concepts = {
        "routesignal": "routesignal",
        "inbound": "inbound",
        "demo": "demo",
        "leads": "leads",
        "owner": "owner",
        "routing": "routing",
        "callback": "callback",
        "handoff": "handoff",
        "manual_tracking": "manual tracking",
        "tracking": "tracking",
        "remind": "remind",
        "reminder": "reminder",
        "visibility": "visibility",
        "manager": "manager",
        "follow-up": "follow-up",
        "workflow": "workflow",
        "gap": "gap",
        "next_step": "next step",
        "price": "price",
        "security": "security",
        "workflow_review": "workflow review",
        "spreadsheet": "spreadsheet",
        "slack": "slack",
    }
    present = {name for name, fragment in concepts.items() if fragment in lowered}
    assert_condition(len(present) >= 3, f"{context} should carry richer sales context, got {present}: {response}")


def assert_sales_emphasis_priority(packet: dict, context: str) -> None:
    voice = packet["packet"]["voice_delivery"]
    cues = voice["prosody"]["prosody_plan"]
    cue_targets = [str(cue.get("target") or cue.get("after") or "").lower() for cue in cues]
    blocked_targets = {
        "hi",
        "hello",
        "do you have a minute",
        "this is northstar",
        "calling from northstar",
    }
    for target in cue_targets:
        assert_condition(
            not any(target.startswith(blocked) for blocked in blocked_targets),
            f"{context} should not emphasize greeting/small-talk targets: {cues}",
        )
    important_fragments = {
        "missed callback",
        "callback",
        "handoff",
        "routing",
        "owner",
        "workflow review",
        "high-level answer",
        "inbound demo",
    }
    assert_condition(
        any(any(fragment in target for fragment in important_fragments) for target in cue_targets),
        f"{context} should prioritize sales-problem emphasis targets: {cues}",
    )
    if any("high-level answer" in target for target in cue_targets):
        return
    emphasis_guard = voice["voice_listening_calibration"]["emphasis_guard"]
    assert_condition(
        emphasis_guard["allowed_emphasis_count"] >= 1,
        f"{context} should allow at least one important sales emphasis cue: {emphasis_guard}",
    )


def assert_no_campaign_depth_regressions(response: str, context: str) -> None:
    lowered = response.lower()
    blocked = {
        "approved pricing facts",
        "candidate_response",
        "decision log",
        "guardrail",
        "internal",
        "price-and-scope",
        "runtime",
    }
    for fragment in blocked:
        assert_condition(fragment not in lowered, f"{context} leaked internal/process wording: {response}")
    unsupported_claims = {
        "guaranteed conversion",
        "guaranteed roi",
        "soc 2 certified",
        "soc2 certified",
        "guaranteed salesforce",
    }
    for fragment in unsupported_claims:
        assert_condition(fragment not in lowered, f"{context} made unsupported campaign claim: {response}")


def validate_turn(packet: dict, *, live_tts: bool, fallback_reason: str) -> None:
    assert_condition(packet["live_demo_id"] == "LIVE-DEMO-001", "Unexpected demo id.")
    assert_condition(packet["provider_agent_used"] is False, "Provider agent must not be used.")
    assert_condition(packet["durable_provider_agent_created"] is False, "No durable provider agent.")
    assert_condition(packet["voice_cloning_used"] is False, "Voice cloning must stay blocked.")
    assert_condition(packet["runtime_behavior_changed"] is False, "Runtime behavior must not change.")
    assert_condition(packet["opens_prod_102"] is False, "Demo must not open PROD-102.")
    assert_condition(packet["asr"]["audio_uploaded_to_python_server"] is False, "Browser audio must not upload to Python.")
    tts = packet["packet"]["tts_delivery"]
    voice = packet["packet"]["voice_delivery"]
    summary = packet["summary"]
    assert_condition(tts["provider_key"] == "elevenlabs", "Unexpected TTS provider.")
    assert_condition(tts["live_call_requested"] is live_tts, "Unexpected live TTS mode.")
    assert_condition(tts["provider_calls_made"] is False, "Validation must not call ElevenLabs.")
    assert_condition(tts["generated_text_sent_to_provider"] is False, "Validation must not send text to provider.")
    assert_condition(tts["audio_file_created"] is False, "Validation must not create provider audio.")
    assert_condition(tts["fallback_reason"] == fallback_reason, "Unexpected TTS fallback reason.")
    assert_condition(tts["customer_audio_uploaded"] is False, "Customer audio must not upload to TTS provider.")
    assert_condition(tts["voice_cloning_used"] is False, "TTS must not clone voices.")
    assert_condition(tts["api_key_value_logged"] is False, "API key value must not be logged.")
    assert_condition(tts["voice_id_value_logged"] is False, "Voice ID value must not be logged.")
    assert_condition(tts["validation"]["passed"] is True, "TTS boundary validation should pass.")
    assert_no_tts_word_split_breaks(tts["tts_input_text"], "TTS provider text")
    assert_condition(voice["validation"]["passed"] is True, "Runtime voice delivery validation should pass.")
    assert_condition(voice["final_response_unchanged"] is True, "Final response must stay unchanged.")
    assert_condition(summary["final_response"] == packet["packet"]["final_response"], "Summary response mismatch.")
    assert_condition(summary["tts_provider_calls_made"] is False, "Summary should show no provider call.")
    async_enrichment = packet["dialogue_reasoner_async_enrichment"]
    assert_condition(async_enrichment["reasoner_id"] == "DIALOGUE-REASONER-004", "Async enrichment evidence id mismatch.")
    assert_condition(async_enrichment["provider_call_made"] is False, "Live-demo evidence must not call the LLM provider.")
    assert_condition(async_enrichment["text_sent_to_provider"] is False, "Live-demo evidence must not send text to the LLM provider.")
    assert_condition(async_enrichment["api_key_value_logged"] is False, "Async enrichment must not log API key values.")
    assert_condition(async_enrichment["customer_response_blocked_on_provider"] is False, "Async enrichment must not block customer response.")
    assert_condition(async_enrichment["provider_result_applied_after_response"] is False, "Dry live-demo turn must not apply provider results.")
    assert_condition(async_enrichment["runtime_route_override_allowed"] is False, "Async enrichment must not override runtime route labels.")
    assert_condition(async_enrichment["mutates_final_response"] is False, "Async enrichment must not mutate final response.")
    assert_condition(async_enrichment["final_response_changed_by_provider"] is False, "Async enrichment must not change final response.")
    assert_condition(async_enrichment["opens_prod_102"] is False, "Async enrichment must not open PROD-102.")
    response_snapshot = async_enrichment["customer_response_snapshot"]
    assert_condition(response_snapshot["available_before_provider"] is True, "Final response must exist before async enrichment.")
    assert_condition(response_snapshot["text_logged"] is False, "Async enrichment should store a response fingerprint, not response text.")
    assert_condition(response_snapshot["char_count"] == len(summary["final_response"]), "Response snapshot length mismatch.")
    assert_condition(len(response_snapshot["text_fingerprint"]) == 64, "Response fingerprint should be a SHA-256 hex digest.")


def main() -> None:
    assert_condition(SCRIPT_PATH.exists(), "LIVE-DEMO-001 runner is missing.")
    assert_condition(PROFILE_PATH.exists(), "LIVE-DEMO-001 fictional campaign profile is missing.")
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    assert_condition(profile["profile_id"] == "LIVE-DEMO-001-fictional-b2b-sales-campaign", "Unexpected profile id.")
    assert_condition(profile["applies_to_campaign_id"] == "campaign-prod-005-b2b-software", "Profile must apply to default B2B campaign.")
    assert_condition(profile["fictional_company"]["client_name"] == "Northstar Workflow Labs", "Unexpected fictional company.")
    assert_condition(profile["fictional_company"]["product_name"] == "RouteSignal CRM", "Unexpected fictional product.")
    assert_condition(profile["source_policy"]["reuse_label"] == "inspiration only", "Profile must stay inspiration-only.")
    assert_condition(profile["source_policy"]["directly_copied_material"] == "none", "Profile must not copy source material.")
    profile_source_urls = {source["url"] for source in profile["source_inspiration"]}
    assert_condition(REQUIRED_SOURCE_URLS.issubset(profile_source_urls), f"Profile missing source URLs: {profile_source_urls}")
    for source in profile["source_inspiration"]:
        assert_condition(source["reuse_label"] == "inspiration only", source)
        assert_condition(source["directly_copied_material"] == "none", source)

    exported = run_demo(
        "--export-html",
        str(HTML_OUT),
        "--export-metadata",
        str(METADATA_OUT),
        "--elevenlabs-env-file",
        str(MISSING_LIVE_TTS_ENV_FILE),
    )
    metadata = json.loads(exported.stdout)
    html = HTML_OUT.read_text(encoding="utf-8")
    metadata_file = json.loads(METADATA_OUT.read_text(encoding="utf-8"))
    assert_condition(metadata == metadata_file, "Metadata stdout/file mismatch.")
    assert_condition("SpeechRecognition" in html, "Browser ASR missing.")
    assert_condition("webkitSpeechRecognition" in html, "WebKit ASR fallback missing.")
    assert_condition("Start Conversation" in html, "Auto-conversation start button missing.")
    assert_condition("const AGENT_OPEN_TRANSCRIPT = \"__agent_open__\"" in html, "Agent-led opening marker missing.")
    assert_condition("let sessionStarted = false" in html, "Browser should track whether the agent has opened the session.")
    assert_condition("function startAgentOpening" in html, "Start Conversation should make the agent speak before listening.")
    assert_condition("submitTurn(true, AGENT_OPEN_TRANSCRIPT, \"agent-open\")" in html, "Agent opening should enter the runtime through /turn.")
    assert_condition("transcriptOverride=null" in html, "submitTurn should support runtime-owned synthetic opening turns.")
    assert_condition("inputTypeOverride=\"speech-final\"" in html, "submitTurn should support explicit input types.")
    assert_condition("session_id: sessionId" in html, "Browser session id missing.")
    assert_condition("submitTurn(true)" in html, "Auto-submit after recognition missing.")
    assert_condition("function isWeakAutoTranscript" in html, "Browser STT fragment guard missing.")
    assert_condition("const VOICE_TURN_STATES = Object.freeze" in html, "Voice turn-state controller missing.")
    assert_condition("function setVoiceTurnState" in html, "Voice turn-state setter missing.")
    assert_condition("function stopRecognitionForAgentTurn" in html, "Recognition stop before agent turn missing.")
    assert_condition("function shouldAcceptAutoTranscript" in html, "ASR acceptance gate missing.")
    assert_condition("const FINAL_TRANSCRIPT_SUBMIT_DELAY_MS" in html, "Final transcript debounce setting missing.")
    assert_condition("const TURN_TAKING_POLICY = metadata.browser_asr.turn_taking_policy;" in html, "Runtime ASR turn-taking policy metadata missing.")
    assert_condition("const REQUIRE_FINAL_RESULT_FOR_AUTO_SUBMIT" in html, "Auto-submit should require final ASR results.")
    assert_condition("let lastResultHadFinal = false;" in html, "ASR final-result tracking missing.")
    assert_condition("function clearFinalSubmitTimer" in html, "ASR pending-submit clear helper missing.")
    assert_condition("function scheduleAutoSubmit" in html, "Final transcript debounce helper missing.")
    assert_condition("recognition.continuous = true" in html, "ASR should stay open across short thinking pauses.")
    assert_condition("Listening... waiting for a pause." in html, "ASR should wait for a pause before auto-submitting.")
    assert_condition("const acceptedVoiceTurnState = voiceTurnState" in html, "Accepted voice turn state should be captured before agent thinking state.")
    assert_condition("voice_turn_state: acceptedVoiceTurnState" in html, "Voice turn state should be sent with turn packets.")
    assert_condition("agent_speaking" in html, "Agent-speaking state missing.")
    assert_condition("restartListenAfterAgentOutput" in html, "Post-agent listening restart gate missing.")
    assert_condition("lastTranscriptConfidence" in html, "Browser ASR confidence tracking missing.")
    assert_condition("asr_confidence" in html, "Browser ASR confidence should be sent with turn packets.")
    assert_condition("campaign_options" in html, "Campaign selector metadata missing.")
    assert_condition("/turn" in html, "Turn endpoint missing.")
    assert_condition("audio.src = payload.audio_url" in html, "Browser audio playback missing.")
    assert_condition("audio.volume = AGENT_PLAYBACK_VOLUME" in html, "Agent audio playback volume calibration missing.")
    assert_condition("Browser Fallback Voice" in html, "Fallback speech button missing.")
    assert_condition("utterance.volume = BROWSER_FALLBACK_VOICE_VOLUME" in html, "Browser fallback voice volume calibration missing.")
    assert_condition("let latestSpeechText" in html, "Browser fallback should keep provider-shaped speech text.")
    assert_condition("browser_fallback_speech_text" in html, "Browser fallback should use markup-free TTS text.")
    assert_condition("new SpeechSynthesisUtterance(latestSpeechText)" in html, "Browser fallback must speak runtime TTS input, not raw final_response.")
    assert_condition("let fallbackVoice = null" in html, "Browser fallback should cache one local voice for consistency.")
    assert_condition("function selectFallbackVoice" in html, "Browser fallback voice selector missing.")
    assert_condition("utterance.voice = fallbackVoice" in html, "Browser fallback should pin a consistent local voice when available.")
    assert_condition("const TERMINAL_CALL_CONTROLS" in html, "Terminal call-control set missing.")
    assert_condition("function isTerminalCallControl" in html, "Terminal call-control helper missing.")
    assert_condition("callEnded = isTerminalCallControl(payload.summary.call_control)" in html, "Browser should mark terminal calls after schedule/end decisions.")
    assert_condition("Conversation ended. Listening will not restart." in html, "Terminal call should stop listening restart after goodbye.")
    assert_condition("metadata.tts.live_tts_enabled && payload.summary.tts_provider_calls_made" in html, "Live TTS provider failure should be detected before browser fallback.")
    assert_condition("ElevenLabs audio unavailable" in html, "Provider audio fallback should be visible instead of silent default-voice switching.")
    assert_condition("retrieval_status" in html, "Demo UI should expose guarded retrieval status.")
    assert_condition(metadata["live_demo_id"] == "LIVE-DEMO-001", "Unexpected metadata id.")
    assert_condition(metadata["default_campaign_id"] == "campaign-prod-005-b2b-software", "Default campaign should be English.")
    assert_condition(metadata["fictional_campaign_profile"]["profile_id"] == profile["profile_id"], "Profile metadata missing.")
    assert_condition(metadata["fictional_campaign_profile"]["client_name"] == "Northstar Workflow Labs", "Profile client metadata missing.")
    assert_condition(metadata["fictional_campaign_profile"]["product_name"] == "RouteSignal CRM", "Profile product metadata missing.")
    assert_condition(set(metadata["fictional_campaign_profile"]["source_urls"]) == profile_source_urls, "Profile source metadata mismatch.")
    english_campaigns = [item for item in metadata["campaign_options"] if item["language"] == "en"]
    assert_condition(any(item["campaign_id"] == "campaign-prod-005-b2b-software" for item in english_campaigns), "English campaign option missing.")
    assert_condition(metadata["local_server"]["endpoints"] == ["/", "/metadata", "/campaigns", "/turn", "/audio"], "Endpoint metadata mismatch.")
    assert_condition("generic_campaign_options" in html, "Generic campaign selector metadata missing.")
    assert_condition("campaign_config_path" in html, "Generic campaign config path payload field missing.")
    assert_condition(metadata["repo_owned_agent"]["provider_agent_used"] is False, "Provider agent boundary missing.")
    assert_condition(metadata["repo_owned_agent"]["guarded_retrieval"]["enabled_when_registry_present"] is True, "LIVE-DEMO-001 should wire local guarded retrieval when the registry exists.")
    assert_condition(metadata["repo_owned_agent"]["guarded_retrieval"]["campaign_facts_override_rag"] is True, "Campaign facts must override RAG in the demo.")
    assert_condition(metadata["repo_owned_agent"]["composer_hooks"]["enabled_when_retrieval_enabled"] is True, "Composer hooks should be wired behind guarded retrieval.")
    assert_condition(metadata["tts"]["provider"] == "elevenlabs", "Expected ElevenLabs TTS.")
    assert_condition(metadata["tts"]["api_key_env_var"] == "ELEVENLABS_API_KEY", "ElevenLabs API key env var should be explicit.")
    assert_condition(metadata["tts"]["elevenlabs_env_file"]["path"].endswith("missing-default-elevenlabs.env"), "ElevenLabs env file metadata missing.")
    assert_condition(metadata["tts"]["elevenlabs_env_file"]["present"] is False, "Validation should not require a local ElevenLabs env file.")
    assert_condition("config/local/voice_ids.json" in metadata["tts"]["voice_id_sources"], "Legacy local voice ID path should be documented.")
    assert_condition(metadata["playback"]["agent_audio_volume"] == 0.68, "Agent audio volume should be toned down for live demo playback.")
    assert_condition(metadata["playback"]["browser_fallback_voice_volume"] == 0.68, "Browser fallback voice volume should match live demo playback volume.")
    assert_condition(metadata["playback"]["provider_audio_file_unchanged"] is True, "Volume calibration must not alter provider audio files.")
    assert_condition(metadata["browser_asr"]["audio_sent_to_python_server"] is False, "Audio upload boundary mismatch.")
    assert_condition(metadata["browser_asr"]["acceptance_policy"]["low_confidence_threshold"] == 0.45, "ASR low-confidence threshold missing.")
    assert_condition(metadata["browser_asr"]["acceptance_policy"]["final_transcript_submit_delay_ms"] >= 1800, "ASR final-submit debounce should allow thinking pauses.")
    assert_condition(metadata["browser_asr"]["turn_taking_policy"]["checkpoint_id"] == "LIVE-DEMO-004-realtime-turn-taking-asr-vad", "LIVE-DEMO-004 ASR turn-taking policy missing.")
    assert_condition(metadata["browser_asr"]["turn_taking_policy"]["requires_final_result_for_auto_submit"] is True, "ASR must require a final result before auto-submit.")
    assert_condition(metadata["browser_asr"]["turn_taking_policy"]["submit_on_interim_results"] is False, "ASR must not auto-submit interim results.")
    assert_condition(metadata["turn_taking"]["controller"] == "voice-turn-state-machine", "Turn-taking controller should not be browser-named.")
    assert_condition(metadata["turn_taking"]["listen_while_agent_speaks"] is False, "Demo must not listen while agent speaks.")
    assert_condition(metadata["turn_taking"]["restart_after_agent_output_ms"] >= 650, "Restart delay should leave a gap after agent speech.")
    assert_condition(metadata["boundaries"]["runtime_behavior_changed"] is False, "Runtime boundary mismatch.")
    assert_condition(metadata["boundaries"]["opens_prod_102"] is False, "PROD-102 boundary mismatch.")
    assert_condition(metadata["boundaries"]["stores_turns_under_ignored_private_data"] is True, "Private output boundary missing.")

    LIVE_TTS_ENV_FILE.write_text(
        "ELEVENLABS_API_KEY" + "=test-live-tts-api-key\nUNRELATED_PROVIDER_KEY=ignored\n",
        encoding="utf-8",
    )
    env_exported = run_demo(
        "--export-metadata",
        str(ENV_METADATA_OUT),
        "--elevenlabs-env-file",
        str(LIVE_TTS_ENV_FILE),
    )
    env_metadata = json.loads(env_exported.stdout)
    assert_condition(
        env_metadata["tts"]["elevenlabs_env_file"]["loaded_keys"] == ["ELEVENLABS_API_KEY"],
        "ElevenLabs env loader should load only allowed live TTS keys.",
    )
    assert_condition(
        env_metadata["tts"]["elevenlabs_env_file"]["ignored_keys"] == ["UNRELATED_PROVIDER_KEY"],
        "ElevenLabs env loader should report ignored non-allowlisted keys without using them.",
    )
    assert_condition(env_metadata["tts"]["api_key_present_at_start"] is True, "Loaded env file should satisfy API-key preflight.")
    assert_no_secret_patterns(env_exported.stdout)
    assert_no_secret_patterns(ENV_METADATA_OUT.read_text(encoding="utf-8"))

    live_missing = run_demo_raw(
        "--decision-transcript",
        TRANSCRIPT,
        "--live-tts",
        "--consent-confirmed",
        "--elevenlabs-env-file",
        str(TMP_DIR / "missing-elevenlabs.env"),
    )
    assert_condition(live_missing.returncode != 0, "Live TTS should fail fast when provider config is missing.")
    assert_condition("Missing: ELEVENLABS_API_KEY" in live_missing.stderr, live_missing.stderr)
    assert_no_secret_patterns(live_missing.stderr)

    agent_open_probe = build_turn_packet(
        transcript="__agent_open__",
        campaign_id="campaign-prod-005-b2b-software",
        stage="relevance-check",
        input_type="agent-open",
        silence_count=0,
        cases_path=DEFAULT_CASES_PATH,
        private_out=TMP_DIR,
        live_tts=False,
        force_key_missing=False,
        timeout_seconds=8.0,
        session_id="agent-led-opening-session",
        session_state={"turns": []},
        voice_turn_state="idle",
    )
    validate_turn(agent_open_probe, live_tts=False, fallback_reason="dry-run-mode")
    assert_condition(
        agent_open_probe["demo_session_continuity"]["reason"] == "agent_opening_started",
        f"Agent-led start should route through runtime sales opening: {agent_open_probe['demo_session_continuity']}",
    )
    assert_condition(
        agent_open_probe["demo_session_continuity"].get("dialogue_focus") == "qualification",
        f"Agent-led start should put the session into qualification focus: {agent_open_probe['demo_session_continuity']}",
    )
    assert_sales_opening_response(agent_open_probe["summary"]["final_response"])
    assert_sales_context_depth(agent_open_probe["summary"]["final_response"], "agent-led sales opening")
    assert_sales_emphasis_priority(agent_open_probe, "agent-led sales opening")
    assert_live_demo_response_style(agent_open_probe["summary"]["final_response"], "agent-led sales opening")
    assert_browser_fallback_text_clean(
        agent_open_probe["summary"].get("browser_fallback_speech_text", ""),
        "agent-led sales opening browser fallback",
    )
    assert_opening_identity_fallback_clean(agent_open_probe["summary"].get("browser_fallback_speech_text", ""))

    opening_clarification_state = {
        "turns": [
            {
                "transcript": agent_open_probe["transcript"],
                "summary": agent_open_probe["summary"],
                "continuity": agent_open_probe["demo_session_continuity"],
            }
        ]
    }
    opening_clarification = build_turn_packet(
        transcript="No, I did not really understand what you asked before that.",
        campaign_id="campaign-prod-005-b2b-software",
        stage="relevance-check",
        input_type="speech-final",
        silence_count=0,
        cases_path=DEFAULT_CASES_PATH,
        private_out=TMP_DIR / "private",
        live_tts=False,
        force_key_missing=False,
        timeout_seconds=8.0,
        session_id="agent-led-opening-clarification-session",
        session_state=opening_clarification_state,
        voice_turn_state="listening",
    )
    validate_turn(opening_clarification, live_tts=False, fallback_reason="dry-run-mode")
    assert_condition(
        opening_clarification["demo_session_continuity"]["reason"] == "previous_question_clarified",
        f"Clarification request should explain the previous question instead of continuing qualification: {opening_clarification['demo_session_continuity']}",
    )
    assert_previous_question_clarified(opening_clarification["summary"]["final_response"], "agent-led opening clarification")
    assert_live_demo_response_style(opening_clarification["summary"]["final_response"], "agent-led opening clarification")

    identity_recall_state = {
        "turns": [
            {
                "transcript": agent_open_probe["transcript"],
                "summary": agent_open_probe["summary"],
                "continuity": agent_open_probe["demo_session_continuity"],
            }
        ]
    }
    identity_recall = build_turn_packet(
        transcript="where were you calling from again?",
        campaign_id="campaign-prod-005-b2b-software",
        stage="relevance-check",
        input_type="speech-final",
        silence_count=0,
        cases_path=DEFAULT_CASES_PATH,
        private_out=TMP_DIR / "private",
        live_tts=False,
        force_key_missing=False,
        timeout_seconds=8.0,
        session_id="agent-led-identity-recall-session",
        session_state=identity_recall_state,
        voice_turn_state="listening",
    )
    validate_turn(identity_recall, live_tts=False, fallback_reason="dry-run-mode")
    assert_condition(
        identity_recall["demo_session_continuity"]["reason"] == "caller_identity_recalled",
        f"Caller identity recall should answer the identity question directly: {identity_recall['demo_session_continuity']}",
    )
    assert_caller_identity_recalled(identity_recall["summary"]["final_response"], "caller identity recall")
    assert_live_demo_response_style(identity_recall["summary"]["final_response"], "caller identity recall")

    opening_negative_state = {
        "turns": [
            {
                "transcript": agent_open_probe["transcript"],
                "summary": agent_open_probe["summary"],
                "continuity": agent_open_probe["demo_session_continuity"],
            }
        ]
    }
    opening_negative = build_turn_packet(
        transcript="no",
        campaign_id="campaign-prod-005-b2b-software",
        stage="relevance-check",
        input_type="speech-final",
        silence_count=0,
        cases_path=DEFAULT_CASES_PATH,
        private_out=TMP_DIR / "private",
        live_tts=False,
        force_key_missing=False,
        timeout_seconds=8.0,
        session_id="agent-led-opening-negative-session",
        session_state=opening_negative_state,
        voice_turn_state="listening",
    )
    validate_turn(opening_negative, live_tts=False, fallback_reason="dry-run-mode")
    assert_condition(
        opening_negative["demo_session_continuity"]["reason"] == "ambiguous_negative_clarified",
        f"Short negative reply should clarify what the buyer rejected: {opening_negative['demo_session_continuity']}",
    )
    assert_negative_reply_clarified(opening_negative["summary"]["final_response"], "agent-led opening negative")
    assert_live_demo_response_style(opening_negative["summary"]["final_response"], "agent-led opening negative")

    qualification_state = {
        "turns": [
            {
                "transcript": agent_open_probe["transcript"],
                "summary": agent_open_probe["summary"],
                "continuity": agent_open_probe["demo_session_continuity"],
            }
        ]
    }
    qualification_ack = build_turn_packet(
        transcript="okay",
        campaign_id="campaign-prod-005-b2b-software",
        stage="relevance-check",
        input_type="speech-final",
        silence_count=0,
        cases_path=DEFAULT_CASES_PATH,
        private_out=TMP_DIR,
        live_tts=False,
        force_key_missing=False,
        timeout_seconds=8.0,
        session_id="agent-led-opening-session",
        session_state=qualification_state,
        voice_turn_state="listening",
    )
    validate_turn(qualification_ack, live_tts=False, fallback_reason="dry-run-mode")
    qualification_ack_continuity = qualification_ack["demo_session_continuity"]
    qualification_ack_dialogue = qualification_ack.get("dialogue_manager") or {}
    qualification_ack_frame = qualification_ack.get("universal_policy_frame") or qualification_ack_dialogue.get("universal_policy_frame") or {}
    qualification_ack_semantics = (
        qualification_ack_continuity.get("contextual_buyer_semantics")
        or qualification_ack_dialogue.get("contextual_buyer_semantics")
        or {}
    )
    assert_condition(
        qualification_ack_continuity["reason"] == "contextual_permission_acknowledgement"
        or (
            qualification_ack_continuity["reason"] == "universal_response_shape_enforced"
            and qualification_ack_frame.get("buyer_move_id") == "permission_acknowledgement"
            and qualification_ack_frame.get("response_shape_enforced_category") == "pain_progression"
        ),
        f"Weak reply after agent opening should keep contextual permission continuity: {qualification_ack_continuity}",
    )
    assert_condition(
        qualification_ack_semantics.get("semantic") == "permission_acknowledgement"
        or qualification_ack_frame.get("buyer_move_id") == "permission_acknowledgement",
        f"Weak reply should be interpreted as permission acknowledgement: semantics={qualification_ack_semantics}, frame={qualification_ack_frame}",
    )
    assert_condition(
        qualification_ack_semantics.get("action_id") == "continue_with_session_policy"
        or qualification_ack_continuity.get("action_id") == "continue_with_session_policy",
        f"Weak reply should continue through session policy: semantics={qualification_ack_semantics}, continuity={qualification_ack_continuity}",
    )
    assert_seller_led_next_move(qualification_ack["summary"]["final_response"], "agent-led acknowledgement")
    assert_contains_any(
        qualification_ack["summary"]["final_response"],
        {"callback", "callbacks", "handoff", "handoffs", "routing", "missed follow-up", "demo follow-up", "follow-up slipping"},
        "agent-led acknowledgement",
    )
    assert_sales_context_depth(qualification_ack["summary"]["final_response"], "agent-led acknowledgement")
    assert_sales_emphasis_priority(qualification_ack, "agent-led acknowledgement")
    assert_live_demo_response_style(qualification_ack["summary"]["final_response"], "agent-led acknowledgement")

    qualification_negative_state = {
        "turns": [
            {
                "transcript": agent_open_probe["transcript"],
                "summary": agent_open_probe["summary"],
                "continuity": agent_open_probe["demo_session_continuity"],
            },
            {
                "transcript": qualification_ack["transcript"],
                "summary": qualification_ack["summary"],
                "continuity": qualification_ack["demo_session_continuity"],
            },
        ]
    }
    qualification_negative = build_turn_packet(
        transcript="no",
        campaign_id="campaign-prod-005-b2b-software",
        stage="relevance-check",
        input_type="speech-final",
        silence_count=0,
        cases_path=DEFAULT_CASES_PATH,
        private_out=TMP_DIR / "private",
        live_tts=False,
        force_key_missing=False,
        timeout_seconds=8.0,
        session_id="agent-led-qualification-negative-session",
        session_state=qualification_negative_state,
        voice_turn_state="listening",
    )
    validate_turn(qualification_negative, live_tts=False, fallback_reason="dry-run-mode")
    assert_condition(
        qualification_negative["demo_session_continuity"]["reason"] == "ambiguous_negative_clarified",
        f"Negative reply after qualification should clarify instead of advancing sales copy: {qualification_negative['demo_session_continuity']}",
    )
    assert_negative_reply_clarified(qualification_negative["summary"]["final_response"], "agent-led qualification negative")
    assert_live_demo_response_style(qualification_negative["summary"]["final_response"], "agent-led qualification negative")

    security_state = {"turns": []}
    security_boundary = build_turn_packet(
        transcript="Does it have SOC 2?",
        campaign_id="campaign-prod-005-b2b-software",
        stage="relevance-check",
        input_type="speech-final",
        silence_count=0,
        cases_path=DEFAULT_CASES_PATH,
        private_out=TMP_DIR / "private",
        live_tts=False,
        force_key_missing=False,
        timeout_seconds=8.0,
        session_id="security-boundary-followup-session",
        session_state=security_state,
        voice_turn_state="listening",
    )
    security_state["turns"].append(
        {
            "transcript": security_boundary["transcript"],
            "summary": security_boundary["summary"],
            "continuity": security_boundary["demo_session_continuity"],
        }
    )
    security_followup = build_turn_packet(
        transcript="what else should I know?",
        campaign_id="campaign-prod-005-b2b-software",
        stage="relevance-check",
        input_type="speech-final",
        silence_count=0,
        cases_path=DEFAULT_CASES_PATH,
        private_out=TMP_DIR / "private",
        live_tts=False,
        force_key_missing=False,
        timeout_seconds=8.0,
        session_id="security-boundary-followup-session",
        session_state=security_state,
        voice_turn_state="listening",
    )
    validate_turn(security_followup, live_tts=False, fallback_reason="dry-run-mode")
    assert_condition(
        security_followup["summary"]["final_response"] != "Thanks. I will keep the next step narrow and avoid repeating the same question.",
        f"Security follow-up should not leak anti-loop repair wording: {security_followup['summary']['final_response']}",
    )
    assert_no_campaign_depth_regressions(security_followup["summary"]["final_response"], "security follow-up")
    assert_live_demo_response_style(security_followup["summary"]["final_response"], "security follow-up")

    qualification_state["turns"].append(
        {
            "transcript": qualification_ack["transcript"],
            "summary": qualification_ack["summary"],
            "continuity": qualification_ack["demo_session_continuity"],
        }
    )
    qualification_gap = build_turn_packet(
        transcript="handoffs are the problem",
        campaign_id="campaign-prod-005-b2b-software",
        stage="relevance-check",
        input_type="speech-final",
        silence_count=0,
        cases_path=DEFAULT_CASES_PATH,
        private_out=TMP_DIR,
        live_tts=False,
        force_key_missing=False,
        timeout_seconds=8.0,
        session_id="agent-led-opening-session",
        session_state=qualification_state,
        voice_turn_state="listening",
    )
    validate_turn(qualification_gap, live_tts=False, fallback_reason="dry-run-mode")
    qualification_gap_continuity = qualification_gap["demo_session_continuity"]
    qualification_gap_dialogue = qualification_gap.get("dialogue_manager") or {}
    qualification_gap_frame = qualification_gap.get("universal_policy_frame") or qualification_gap_dialogue.get("universal_policy_frame") or {}
    qualification_gap_semantics = (
        qualification_gap_continuity.get("contextual_buyer_semantics")
        or qualification_gap_dialogue.get("contextual_buyer_semantics")
        or {}
    )
    assert_condition(
        qualification_gap_continuity["reason"] == "contextual_pain_confirmed"
        or (
            qualification_gap_continuity["reason"] == "universal_response_shape_enforced"
            and qualification_gap_frame.get("buyer_move_id") == "pain_confirmed"
            and qualification_gap_frame.get("sales_progression_stage") == "pain_confirmed_needs_implication"
        ),
        f"Named gap after agent opening should map through contextual pain confirmation: {qualification_gap_continuity}",
    )
    assert_condition(
        qualification_gap_semantics.get("semantic") == "pain_confirmed",
        f"Named gap should be semantically confirmed as pain: {qualification_gap_semantics}",
    )
    assert_condition(
        qualification_gap_semantics.get("target_gap") == "handoffs",
        f"Named gap should target handoffs: {qualification_gap_semantics}",
    )
    assert_condition(
        qualification_gap_semantics.get("playbook_id") == "ROUTESIGNAL-DIAGNOSTIC-PLAYBOOK-001",
        f"Named gap should stay on RouteSignal playbook: {qualification_gap_semantics}",
    )
    assert_condition(
        qualification_gap_semantics.get("action_id") == "request_appointment_time"
        or (
            qualification_gap_continuity.get("action_id") == "continue_with_session_policy"
            and qualification_gap_frame.get("implication_check_required") is True
        ),
        f"Named gap should develop implication before a workflow review time: semantics={qualification_gap_semantics}, frame={qualification_gap_frame}",
    )
    assert_contains_any(
        qualification_gap["summary"]["final_response"],
        {"handoffs", "missed ownership", "extra tracking", "short workflow review", "next step"},
        "agent-led gap close",
    )
    assert_seller_led_next_move(qualification_gap["summary"]["final_response"], "agent-led gap close")
    assert_sales_context_depth(qualification_gap["summary"]["final_response"], "agent-led gap close")
    assert_sales_emphasis_priority(qualification_gap, "agent-led gap close")

    qualification_callback_gap = build_turn_packet(
        transcript="I have to say it's probably the callbacks",
        campaign_id="campaign-prod-005-b2b-software",
        stage="relevance-check",
        input_type="speech-final",
        silence_count=0,
        cases_path=DEFAULT_CASES_PATH,
        private_out=TMP_DIR,
        live_tts=False,
        force_key_missing=False,
        timeout_seconds=8.0,
        session_id="agent-led-callback-gap-session",
        session_state=qualification_state,
        voice_turn_state="listening",
    )
    validate_turn(qualification_callback_gap, live_tts=False, fallback_reason="dry-run-mode")
    assert_condition(
        qualification_callback_gap["demo_session_continuity"]["reason"]
        in {"seller_gap_selected_for_qualification", "seller_gap_selected_for_pain_progression"},
        f"Callback gap after qualification should map to value instead of scheduling: {qualification_callback_gap['demo_session_continuity']}",
    )
    assert_condition(
        qualification_callback_gap["demo_session_continuity"].get("dialogue_focus")
        in {"qualification", "pain_progression"},
        f"Callback gap should preserve qualification focus: {qualification_callback_gap['demo_session_continuity']}",
    )
    assert_condition(
        qualification_callback_gap["summary"]["sales_difficulty"] != "callback-request",
        f"Workflow callback mention should not classify as callback scheduling: {qualification_callback_gap['summary']}",
    )
    assert_callback_workflow_not_scheduling(
        qualification_callback_gap["summary"]["final_response"],
        "agent-led callback gap",
    )
    assert_seller_led_next_move(qualification_callback_gap["summary"]["final_response"], "agent-led callback gap")
    assert_sales_context_depth(qualification_callback_gap["summary"]["final_response"], "agent-led callback gap")
    assert_sales_emphasis_priority(qualification_callback_gap, "agent-led callback gap")
    assert_live_demo_response_style(qualification_callback_gap["summary"]["final_response"], "agent-led callback gap")

    callback_clarification_state = {
        "turns": [
            {
                "transcript": agent_open_probe["transcript"],
                "summary": agent_open_probe["summary"],
                "continuity": agent_open_probe["demo_session_continuity"],
            },
            {
                "transcript": qualification_ack["transcript"],
                "summary": qualification_ack["summary"],
                "continuity": qualification_ack["demo_session_continuity"],
            },
            {
                "transcript": qualification_callback_gap["transcript"],
                "summary": qualification_callback_gap["summary"],
                "continuity": qualification_callback_gap["demo_session_continuity"],
            },
        ]
    }
    callback_clarification = build_turn_packet(
        transcript="what do you mean by callbacks",
        campaign_id="campaign-prod-005-b2b-software",
        stage="relevance-check",
        input_type="speech-final",
        silence_count=0,
        cases_path=DEFAULT_CASES_PATH,
        private_out=TMP_DIR,
        live_tts=False,
        force_key_missing=False,
        timeout_seconds=8.0,
        session_id="agent-led-callback-gap-session",
        session_state=callback_clarification_state,
        voice_turn_state="listening",
    )
    validate_turn(callback_clarification, live_tts=False, fallback_reason="dry-run-mode")
    assert_condition(
        callback_clarification["demo_session_continuity"]["reason"] == "callback_workflow_clarified",
        f"Callback clarification should explain the workflow term, not ask for a time: {callback_clarification['demo_session_continuity']}",
    )
    assert_condition(
        callback_clarification["summary"]["sales_difficulty"] != "callback-request",
        f"Callback clarification should not classify as scheduling: {callback_clarification['summary']}",
    )
    assert_callback_workflow_not_scheduling(
        callback_clarification["summary"]["final_response"],
        "callback workflow clarification",
    )
    assert_seller_led_next_move(callback_clarification["summary"]["final_response"], "callback workflow clarification")
    assert_sales_context_depth(callback_clarification["summary"]["final_response"], "callback workflow clarification")
    assert_live_demo_response_style(callback_clarification["summary"]["final_response"], "callback workflow clarification")

    live_failure_state = {
        "turns": [
            {
                "transcript": agent_open_probe["transcript"],
                "summary": agent_open_probe["summary"],
                "continuity": agent_open_probe["demo_session_continuity"],
            },
            {
                "transcript": qualification_ack["transcript"],
                "summary": qualification_ack["summary"],
                "continuity": qualification_ack["demo_session_continuity"],
            },
            {
                "transcript": callback_clarification["transcript"],
                "summary": callback_clarification["summary"],
                "continuity": callback_clarification["demo_session_continuity"],
            },
        ]
    }
    live_failure_cases = [
        (
            "new trial request clarification",
            "what do you mean by new trial request",
            "conversation_stability_repaired",
            {"failed_to_explain_previous_question"},
            {"inbound demo", "trial inquiries", "owner"},
        ),
        (
            "value relevance clarification",
            "no I don't understand what this means for us I'm asking you",
            "contextual_confusion_not_clear",
            set(),
            {"inbound demo", "callbacks", "missed"},
        ),
        (
            "buyer did not ask question",
            "I didn't ask a question",
            "buyer_no_question_recovered",
            set(),
            {"you did not ask", "I called to check", "inbound demo"},
        ),
        (
            "short topic confusion fragment",
            "I don't know what",
            "topic_confusion_repaired",
            set(),
            {"lost the thread", "demo follow-up", "should I stop"},
        ),
    ]
    seen_failure_responses = {turn["summary"]["final_response"] for turn in live_failure_state["turns"]}
    for context, transcript_text, expected_reason, expected_violations, expected_fragments in live_failure_cases:
        packet = build_turn_packet(
            transcript=transcript_text,
            campaign_id="campaign-prod-005-b2b-software",
            stage="relevance-check",
            input_type="speech-final",
            silence_count=0,
            cases_path=DEFAULT_CASES_PATH,
            private_out=TMP_DIR,
            live_tts=False,
            force_key_missing=False,
            timeout_seconds=8.0,
            session_id="live-demo-003-failure-regression-session",
            session_state=live_failure_state,
            voice_turn_state="listening",
        )
        validate_turn(packet, live_tts=False, fallback_reason="dry-run-mode")
        assert_condition(
            packet["demo_session_continuity"]["reason"] == expected_reason,
            f"{context} should route to the specific live failure repair: {packet['demo_session_continuity']}",
        )
        actual_violations = set(packet["demo_session_continuity"].get("violations") or [])
        assert_condition(
            expected_violations.issubset(actual_violations),
            f"{context} should report expected repair violations {expected_violations}: {packet['demo_session_continuity']}",
        )
        assert_condition(
            packet["summary"]["final_response"] not in seen_failure_responses,
            f"{context} repeated a prior response: {packet['summary']['final_response']}",
        )
        assert_contains_any(packet["summary"]["final_response"], expected_fragments, context)
        assert_no_generic_focus_menu(packet["summary"]["final_response"], context)
        assert_live_demo_response_style(packet["summary"]["final_response"], context)
        seen_failure_responses.add(packet["summary"]["final_response"])
        live_failure_state["turns"].append(
            {
                "transcript": packet["transcript"],
                "summary": packet["summary"],
                "continuity": packet["demo_session_continuity"],
            }
        )

    buyer_stop_packet = build_turn_packet(
        transcript="yeah let's just stop here I don't want to talk about this one more",
        campaign_id="campaign-prod-005-b2b-software",
        stage="relevance-check",
        input_type="speech-final",
        silence_count=0,
        cases_path=DEFAULT_CASES_PATH,
        private_out=TMP_DIR,
        live_tts=False,
        force_key_missing=False,
        timeout_seconds=8.0,
        session_id="live-demo-003-failure-regression-session",
        session_state=live_failure_state,
        voice_turn_state="listening",
    )
    validate_turn(buyer_stop_packet, live_tts=False, fallback_reason="dry-run-mode")
    buyer_stop_continuity = buyer_stop_packet["demo_session_continuity"]
    buyer_stop_semantics = buyer_stop_continuity.get("contextual_buyer_semantics") or {}
    assert_condition(
        buyer_stop_continuity["reason"] == "contextual_stop_request",
        f"Buyer stop request should be respected before sales progression: {buyer_stop_continuity}",
    )
    assert_condition(
        buyer_stop_semantics.get("semantic") == "stop_request",
        f"Buyer stop request should use stop-request semantics: {buyer_stop_semantics}",
    )
    assert_condition(
        buyer_stop_semantics.get("action_id") == "end_call_stop_request",
        f"Buyer stop request should end through the semantic action: {buyer_stop_semantics}",
    )
    assert_condition(
        buyer_stop_packet["summary"]["call_control"] == "end-call",
        f"Buyer stop request should end the call: {buyer_stop_packet['summary']}",
    )
    assert_condition(
        "written summary" not in buyer_stop_packet["summary"]["final_response"].lower(),
        f"Buyer stop request should not keep selling: {buyer_stop_packet['summary']['final_response']}",
    )

    call_context_state = {
        "turns": [
            {
                "transcript": agent_open_probe["transcript"],
                "summary": agent_open_probe["summary"],
                "continuity": agent_open_probe["demo_session_continuity"],
            }
        ]
    }
    call_context_transcripts = [
        ("time constrained agenda", "I don't have a lot of time right now what do you want exactly", "time_constrained_agenda_answered"),
        ("buyer expects agent lead", "I don't have a question you called me so you should ask whatever you want to ask", "buyer_no_question_recovered"),
        ("next step scope", "what is the next step", "workflow_review_next_step_explained"),
        ("workflow review scope", "how short is this workflow review that you're talking about", "workflow_review_scope_explained"),
        ("time waste friction", "seems to me like you are wasting time right now", "time_waste_repair_offered"),
        ("unknown gap", "I don't know", "uncertain_gap_simplified"),
        ("not understanding topic", "right I don't know what you're talking about", "topic_confusion_repaired"),
        ("frustrated confusion", "the fuck", "frustration_confusion_repaired"),
    ]
    call_context_responses = []
    for context, transcript_text, expected_reason in call_context_transcripts:
        packet = build_turn_packet(
            transcript=transcript_text,
            campaign_id="campaign-prod-005-b2b-software",
            stage="relevance-check",
            input_type="speech-final",
            silence_count=0,
            cases_path=DEFAULT_CASES_PATH,
            private_out=TMP_DIR,
            live_tts=False,
            force_key_missing=False,
            timeout_seconds=8.0,
            session_id="agent-led-call-context-session",
            session_state=call_context_state,
            voice_turn_state="listening",
        )
        validate_turn(packet, live_tts=False, fallback_reason="dry-run-mode")
        assert_condition(
            packet["demo_session_continuity"]["reason"] == expected_reason,
            f"{context} should use a call-context recovery route: {packet['demo_session_continuity']}",
        )
        assert_call_context_recovered(packet["summary"]["final_response"], context)
        assert_sales_context_depth(packet["summary"]["final_response"], context)
        assert_live_demo_response_style(packet["summary"]["final_response"], context)
        call_context_responses.append(packet["summary"]["final_response"])
        call_context_state["turns"].append(
            {
                "transcript": packet["transcript"],
                "summary": packet["summary"],
                "continuity": packet["demo_session_continuity"],
            }
        )
    assert_condition(
        len(call_context_responses) == len(set(call_context_responses)),
        f"Call-context recovery should not repeat the same response: {call_context_responses}",
    )

    qualification_variety_state = {
        "turns": [
            {
                "transcript": agent_open_probe["transcript"],
                "summary": agent_open_probe["summary"],
                "continuity": agent_open_probe["demo_session_continuity"],
            }
        ]
    }
    qualification_variety_packets = []
    for transcript_text in ["okay", "tell me more", "what else should I know", "why does that matter", "how would it help"]:
        packet = build_turn_packet(
            transcript=transcript_text,
            campaign_id="campaign-prod-005-b2b-software",
            stage="relevance-check",
            input_type="speech-final",
            silence_count=0,
            cases_path=DEFAULT_CASES_PATH,
            private_out=TMP_DIR,
            live_tts=False,
            force_key_missing=False,
            timeout_seconds=8.0,
            session_id="agent-led-variety-session",
            session_state=qualification_variety_state,
            voice_turn_state="listening",
        )
        qualification_variety_packets.append(packet)
        qualification_variety_state["turns"].append(
            {
                "transcript": packet["transcript"],
                "summary": packet["summary"],
                "continuity": packet["demo_session_continuity"],
            }
        )
        validate_turn(packet, live_tts=False, fallback_reason="dry-run-mode")
        assert_sales_context_depth(packet["summary"]["final_response"], f"qualification variety {transcript_text}")
        assert_seller_led_next_move(packet["summary"]["final_response"], f"qualification variety {transcript_text}")
        assert_sales_emphasis_priority(packet, f"qualification variety {transcript_text}")
        assert_live_demo_response_style(packet["summary"]["final_response"], f"qualification variety {transcript_text}")
    variety_responses = [packet["summary"]["final_response"] for packet in qualification_variety_packets]
    assert_condition(
        len(variety_responses) == len(set(variety_responses)),
        f"Qualification steering should have enough response variety for repeated live follow-ups: {variety_responses}",
    )
    concept_fragments = {
        "inbound",
        "demo",
        "owner",
        "routing",
        "callback",
        "handoff",
        "reminder",
        "visibility",
        "manager",
        "spreadsheet",
        "slack",
    }
    observed_concepts = {
        fragment
        for response in variety_responses
        for fragment in concept_fragments
        if fragment in response.lower()
    }
    assert_condition(
        len(observed_concepts) >= 7,
        f"Qualification steering should cover a wider sales context set, got {observed_concepts}: {variety_responses}",
    )

    opening_probe = build_turn_packet(
        transcript="hey what's up",
        campaign_id="campaign-prod-005-b2b-software",
        stage="relevance-check",
        input_type="speech-final",
        silence_count=0,
        cases_path=DEFAULT_CASES_PATH,
        private_out=TMP_DIR,
        live_tts=False,
        force_key_missing=False,
        timeout_seconds=8.0,
        session_id="sales-opening-session",
        session_state={"turns": []},
    )
    validate_turn(opening_probe, live_tts=False, fallback_reason="dry-run-mode")
    assert_condition(opening_probe["demo_session_continuity"]["reason"] == "opening_greeting_answered", "Greeting should be handled by the sales opener.")
    assert_sales_opening_response(opening_probe["summary"]["final_response"])
    assert_sales_context_depth(opening_probe["summary"]["final_response"], "sales opening")
    assert_sales_emphasis_priority(opening_probe, "sales opening")
    assert_live_demo_response_style(opening_probe["summary"]["final_response"], "sales opening")

    dry_packet = json.loads(
        run_demo("--decision-transcript", TRANSCRIPT, "--decision-out", str(DRY_OUT)).stdout
    )
    file_packet = json.loads(DRY_OUT.read_text(encoding="utf-8"))
    assert_condition(dry_packet == file_packet, "Dry-run stdout/file mismatch.")
    validate_turn(dry_packet, live_tts=False, fallback_reason="dry-run-mode")
    assert_condition(dry_packet["turn_taking"]["voice_turn_state_received"] is None, "CLI dry-run should not invent voice turn state.")
    assert_condition(dry_packet["turn_taking"]["listen_while_agent_speaks"] is False, "Turn policy should block listening while agent speaks.")
    assert_condition(dry_packet["asr"]["quality_gate"]["accepted"] is True, "Normal dry-run transcript should pass ASR quality gate.")

    forced_packet = json.loads(
        run_demo(
            "--decision-transcript",
            TRANSCRIPT,
            "--live-tts",
            "--force-key-missing",
            "--consent-confirmed",
            "--decision-out",
            str(FORCED_OUT),
        ).stdout
    )
    validate_turn(forced_packet, live_tts=True, fallback_reason="forced-key-missing")

    runtime_upgrade_packet = build_turn_packet(
        transcript="I am not sure this is worth the price",
        campaign_id="campaign-prod-005-b2b-software",
        stage="relevance-check",
        input_type="speech-final",
        silence_count=0,
        cases_path=DEFAULT_CASES_PATH,
        private_out=TMP_DIR / "private",
        live_tts=False,
        force_key_missing=False,
        timeout_seconds=8.0,
        session_id="audible-runtime-upgrade-session",
        session_state={"turns": []},
        asr_confidence=0.91,
        voice_turn_state="listening",
    )
    validate_turn(runtime_upgrade_packet, live_tts=False, fallback_reason="dry-run-mode")
    runtime_summary = runtime_upgrade_packet["summary"]
    runtime_packet = runtime_upgrade_packet["packet"]
    assert_condition(runtime_summary["retrieval_status"] == "influenced", runtime_summary)
    assert_condition(runtime_summary["retrieval_used_in_runtime"] is True, runtime_summary)
    assert_condition(runtime_summary["retrieved_item_ids"], runtime_summary)
    assert_condition(runtime_packet["core_pack"]["ethical_persuasion_allowed"] is True, runtime_packet["core_pack"])
    assert_condition(runtime_packet["core_pack"]["campaign_facts_override_rag"] is True, runtime_packet["core_pack"])
    assert_contains_any(runtime_summary["final_response"], {"$29/month", "$59/month", "missed follow-up"}, "audible runtime upgrade")
    assert_condition(runtime_summary["tts_input_source"] == "provider_rendered_text", runtime_summary)
    assert_condition(runtime_summary["browser_fallback_speech_text"] != runtime_summary["final_response"], runtime_summary)
    assert_browser_fallback_text_clean(
        runtime_summary["browser_fallback_speech_text"],
        "audible runtime upgrade",
    )
    assert_contains_any(runtime_summary["browser_fallback_speech_text"], {"um,", "so,", "well,"}, "audible runtime fallback text")
    assert_condition(
        runtime_packet["voice_delivery"]["speech_realism"]["bundle_count"] >= 1,
        runtime_packet["voice_delivery"]["speech_realism"],
    )

    low_confidence_packet = build_turn_packet(
        transcript="what does your product actually do",
        campaign_id="campaign-prod-005-b2b-software",
        stage="relevance-check",
        input_type="speech-final",
        silence_count=0,
        cases_path=DEFAULT_CASES_PATH,
        private_out=TMP_DIR / "private",
        live_tts=False,
        force_key_missing=False,
        timeout_seconds=8.0,
        session_id="low-confidence-asr-session",
        session_state={"turns": []},
        asr_confidence=0.2,
        voice_turn_state="listening",
    )
    validate_turn(low_confidence_packet, live_tts=False, fallback_reason="dry-run-mode")
    assert_condition(low_confidence_packet["asr"]["quality_gate"]["accepted"] is False, "Low confidence transcript should be rejected.")
    assert_condition(low_confidence_packet["asr"]["quality_gate"]["reason"] == "low_confidence", "Low confidence reason missing.")
    assert_condition(
        "repeat" in low_confidence_packet["summary"]["final_response"].lower()
        or "catch" in low_confidence_packet["summary"]["final_response"].lower(),
        f"Low confidence response should ask for repeat: {low_confidence_packet['summary']['final_response']}",
    )
    assert_condition(
        low_confidence_packet["demo_session_continuity"]["reason"] == "asr_low_confidence_repair",
        f"Low confidence should not enter sales logic: {low_confidence_packet['demo_session_continuity']}",
    )

    clear_confidence_packet = build_turn_packet(
        transcript="what does your product actually do",
        campaign_id="campaign-prod-005-b2b-software",
        stage="relevance-check",
        input_type="speech-final",
        silence_count=0,
        cases_path=DEFAULT_CASES_PATH,
        private_out=TMP_DIR / "private",
        live_tts=False,
        force_key_missing=False,
        timeout_seconds=8.0,
        session_id="clear-confidence-asr-session",
        session_state={"turns": []},
        asr_confidence=0.82,
        voice_turn_state="listening",
    )
    validate_turn(clear_confidence_packet, live_tts=False, fallback_reason="dry-run-mode")
    assert_condition(clear_confidence_packet["asr"]["quality_gate"]["accepted"] is True, "Clear confidence transcript should pass ASR quality gate.")
    assert_condition(
        clear_confidence_packet["demo_session_continuity"]["reason"] == "campaign_depth_product_explanation_answered",
        f"Clear confidence should enter campaign logic: {clear_confidence_packet['demo_session_continuity']}",
    )

    stale_greeting_packet = build_turn_packet(
        transcript="hey what's up",
        campaign_id="campaign-prod-005-b2b-software",
        stage="relevance-check",
        input_type="speech-final",
        silence_count=0,
        cases_path=DEFAULT_CASES_PATH,
        private_out=TMP_DIR / "private",
        live_tts=False,
        force_key_missing=False,
        timeout_seconds=8.0,
        session_id="stale-greeting-session",
        session_state={
            "turns": [
                {
                    "transcript": "older unclear turn",
                    "summary": {"final_response": "Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?"},
                    "continuity": {"applied": False, "reason": "no_session_continuity_match"},
                }
            ]
        },
        asr_confidence=0.95,
        voice_turn_state="listening",
    )
    assert_condition(
        stale_greeting_packet["demo_session_continuity"]["reason"] == "opening_greeting_answered",
        f"Stale-session greeting should not fall into the generic focus menu: {stale_greeting_packet['demo_session_continuity']}",
    )
    assert_sales_opening_response(stale_greeting_packet["summary"]["final_response"])
    assert_condition(
        not response_reopens_focus_menu(stale_greeting_packet["summary"]["final_response"]),
        f"Stale-session greeting reopened generic menu: {stale_greeting_packet['summary']['final_response']}",
    )
    validate_turn(stale_greeting_packet, live_tts=False, fallback_reason="dry-run-mode")

    direct_price_packet = build_turn_packet(
        transcript="How much does it cost?",
        campaign_id="campaign-prod-005-b2b-software",
        stage="relevance-check",
        input_type="speech-final",
        silence_count=0,
        cases_path=DEFAULT_CASES_PATH,
        private_out=TMP_DIR / "private",
        live_tts=False,
        force_key_missing=False,
        timeout_seconds=8.0,
        session_id="direct-price-seller-led-session",
        session_state={"turns": []},
    )
    direct_price_response = direct_price_packet["summary"]["final_response"]
    assert_condition(
        direct_price_response.lower().startswith("starter is $29/month"),
        f"Direct price question should answer price before steering discovery: {direct_price_packet['summary']}",
    )
    assert_condition(
        "$29/month" in direct_price_response and "$59/month" in direct_price_response,
        f"Direct price question should include approved demo prices: {direct_price_response}",
    )
    assert_seller_led_next_move(direct_price_response, "direct price answer")
    assert_seller_led_next_move(
        direct_price_packet["summary"].get("browser_fallback_speech_text", ""),
        "direct price browser fallback",
    )
    validate_turn(direct_price_packet, live_tts=False, fallback_reason="dry-run-mode")

    voice_consistency_state = {"turns": []}
    voice_settings_by_turn = []
    for transcript in [
        "hey what's up",
        "I want to talk about the price",
        "handoffs",
        "you should call me 10 a.m. tomorrow",
    ]:
        packet = build_turn_packet(
            transcript=transcript,
            campaign_id="campaign-prod-005-b2b-software",
            stage="relevance-check",
            input_type="speech-final",
            silence_count=0,
            cases_path=DEFAULT_CASES_PATH,
            private_out=TMP_DIR,
            live_tts=False,
            force_key_missing=False,
            timeout_seconds=8.0,
            session_id="voice-consistency-session",
            session_state=voice_consistency_state,
            asr_confidence=0.95,
            voice_turn_state="listening",
        )
        validate_turn(packet, live_tts=False, fallback_reason="dry-run-mode")
        voice_settings_by_turn.append(packet["packet"]["tts_delivery"]["voice_settings"])
        voice_consistency_state["turns"].append(
            {
                "transcript": packet["transcript"],
                "summary": packet["summary"],
                "continuity": packet["demo_session_continuity"],
            }
        )
    assert_condition(
        len({json.dumps(settings, sort_keys=True) for settings in voice_settings_by_turn}) == 1,
        f"Live-demo voice settings should stay stable across mixed turn types: {voice_settings_by_turn}",
    )

    session_state = {"turns": []}
    first = build_turn_packet(
        transcript="I am mainly concerned about the price and whether this is worth the effort.",
        campaign_id="campaign-prod-005-b2b-software",
        stage="relevance-check",
        input_type="speech-final",
        silence_count=0,
        cases_path=DEFAULT_CASES_PATH,
        private_out=TMP_DIR / "private",
        live_tts=False,
        force_key_missing=False,
        timeout_seconds=8.0,
        session_id="validator-session",
        session_state=session_state,
    )
    session_state["turns"].append(
        {"transcript": first["transcript"], "summary": first["summary"], "continuity": first["demo_session_continuity"]}
    )
    second = build_turn_packet(
        transcript="price",
        campaign_id="campaign-prod-005-b2b-software",
        stage="relevance-check",
        input_type="speech-final",
        silence_count=0,
        cases_path=DEFAULT_CASES_PATH,
        private_out=TMP_DIR / "private",
        live_tts=False,
        force_key_missing=False,
        timeout_seconds=8.0,
        session_id="validator-session",
        session_state=session_state,
    )
    assert_condition(second["demo_session_continuity"]["applied"] is True, "Short price answer should use session continuity.")
    assert_condition(second["summary"]["final_response"] != first["summary"]["final_response"], "Price follow-up should not repeat the same question.")
    assert_condition("$29/month" in second["summary"]["final_response"] and "$59/month" in second["summary"]["final_response"], "Price follow-up response missing demo prices.")
    assert_live_demo_response_style(second["summary"]["final_response"], "short price answer")
    validate_turn(second, live_tts=False, fallback_reason="dry-run-mode")

    session_state["turns"].append({"transcript": second["transcript"], "summary": second["summary"], "continuity": second["demo_session_continuity"]})
    third = build_turn_packet(
        transcript="Yeah, exactly, the price is the problem.",
        campaign_id="campaign-prod-005-b2b-software",
        stage="relevance-check",
        input_type="speech-final",
        silence_count=0,
        cases_path=DEFAULT_CASES_PATH,
        private_out=TMP_DIR / "private",
        live_tts=False,
        force_key_missing=False,
        timeout_seconds=8.0,
        session_id="validator-session",
        session_state=session_state,
    )
    assert_condition(third["demo_session_continuity"]["applied"] is True, "Resolved price focus should persist across later turns.")
    assert_condition("bigger concern" not in third["summary"]["final_response"].lower(), "Resolved price focus must not ask the same choice question again.")
    assert_condition(third["summary"]["final_response"] != second["summary"]["final_response"], "Resolved price focus should advance beyond the pricing sentence.")
    assert_contains_any(third["summary"]["final_response"], {"missed callbacks", "handoff review", "manual chasing", "growth"}, "resolved price follow-up")
    assert_live_demo_response_style(third["summary"]["final_response"], "resolved price follow-up")
    validate_turn(third, live_tts=False, fallback_reason="dry-run-mode")

    explicit_price_state = {"turns": []}
    explicit_price_transcripts = [
        "I want to talk about the price",
        "price",
        "I am asking about the price",
    ]
    explicit_price_packets = []
    for explicit_transcript in explicit_price_transcripts:
        packet = build_turn_packet(
            transcript=explicit_transcript,
            campaign_id="campaign-prod-005-b2b-software",
            stage="relevance-check",
            input_type="speech-final",
            silence_count=0,
            cases_path=DEFAULT_CASES_PATH,
            private_out=TMP_DIR,
            live_tts=False,
            force_key_missing=False,
            timeout_seconds=8.0,
            session_id="explicit-price-session",
            session_state=explicit_price_state,
        )
        explicit_price_packets.append(packet)
        explicit_price_state["turns"].append(
            {
                "transcript": packet["transcript"],
                "summary": packet["summary"],
                "continuity": packet["demo_session_continuity"],
            }
        )
        validate_turn(packet, live_tts=False, fallback_reason="dry-run-mode")
        assert_condition(packet["demo_session_continuity"]["applied"] is True, f"Explicit price turn should not fall back to old menu: {explicit_transcript}")
        assert_condition(not response_reopens_focus_menu(packet["summary"]["final_response"]), f"Explicit price turn reopened menu: {packet['summary']['final_response']}")
        assert_live_demo_response_style(packet["summary"]["final_response"], f"explicit price turn {len(explicit_price_packets)}")
    explicit_price_responses = [packet["summary"]["final_response"] for packet in explicit_price_packets]
    assert_condition(
        "$29/month" in explicit_price_responses[0] and "$59/month" in explicit_price_responses[0],
        f"First explicit price answer should include approved demo prices: {explicit_price_responses}",
    )
    assert_condition(
        len(explicit_price_responses) == len(set(explicit_price_responses)),
        f"Repeated explicit price turns should progress instead of replaying: {explicit_price_responses}",
    )

    proactive_price_state = {"turns": []}
    proactive_price_packets = []
    for proactive_transcript in [
        "I want to talk about the price",
        "hmm okay that is interesting",
        "okay that is interesting",
    ]:
        packet = build_turn_packet(
            transcript=proactive_transcript,
            campaign_id="campaign-prod-005-b2b-software",
            stage="relevance-check",
            input_type="speech-final",
            silence_count=0,
            cases_path=DEFAULT_CASES_PATH,
            private_out=TMP_DIR,
            live_tts=False,
            force_key_missing=False,
            timeout_seconds=8.0,
            session_id="proactive-price-guidance-session",
            session_state=proactive_price_state,
        )
        proactive_price_packets.append(packet)
        proactive_price_state["turns"].append(
            {
                "transcript": packet["transcript"],
                "summary": packet["summary"],
                "continuity": packet["demo_session_continuity"],
            }
        )
        validate_turn(packet, live_tts=False, fallback_reason="dry-run-mode")
        assert_live_demo_response_style(packet["summary"]["final_response"], "proactive price guidance")
    initial_price_response = proactive_price_packets[0]["summary"]["final_response"]
    guidance_responses = [packet["summary"]["final_response"] for packet in proactive_price_packets[1:]]
    assert_condition(
        all(response != initial_price_response for response in guidance_responses),
        f"Low-information acknowledgements after price should not repeat the pricing sentence: {guidance_responses}",
    )
    assert_condition(
        len(guidance_responses) == len(set(guidance_responses)),
        f"Repeated low-information acknowledgements should advance guided selling, not replay: {guidance_responses}",
    )
    assert_contains_any(
        guidance_responses[0],
        {"missed callbacks", "handoff review", "manual chasing", "growth is worth reviewing"},
        "proactive price guidance",
    )
    assert_condition(
        not response_reopens_focus_menu(guidance_responses[0]),
        f"Proactive guidance should not reopen a focus menu: {guidance_responses[0]}",
    )
    for packet in proactive_price_packets[1:]:
        assert_seller_led_next_move(packet["summary"]["final_response"], "proactive price guidance")
        assert_seller_led_next_move(
            packet["summary"].get("browser_fallback_speech_text", ""),
            "proactive price guidance browser fallback",
        )

    guided_topic_sequences = {
        "price": [
            "hey what's up",
            "I want to talk about the price",
            "can you tell me more",
            "what else should I know",
            "okay tell me more",
        ],
        "fit": [
            "hey what's up",
            "let us talk about fit",
            "can you tell me more",
            "what else should I know",
            "okay tell me more",
        ],
        "timing": [
            "hey what's up",
            "timing is my concern",
            "can you tell me more",
            "what else should I know",
            "okay tell me more",
        ],
        "features": [
            "hey what's up",
            "I want to talk about the features",
            "can you tell me more",
            "what else should I know",
            "okay tell me more",
        ],
    }
    for topic, transcripts in guided_topic_sequences.items():
        topic_state = {"turns": []}
        topic_packets = []
        for transcript in transcripts:
            packet = build_turn_packet(
                transcript=transcript,
                campaign_id="campaign-prod-005-b2b-software",
                stage="relevance-check",
                input_type="speech-final",
                silence_count=0,
                cases_path=DEFAULT_CASES_PATH,
                private_out=TMP_DIR,
                live_tts=False,
                force_key_missing=False,
                timeout_seconds=8.0,
                session_id=f"guided-{topic}-sequence",
                session_state=topic_state,
            )
            topic_packets.append(packet)
            topic_state["turns"].append(
                {
                    "transcript": packet["transcript"],
                    "summary": packet["summary"],
                    "continuity": packet["demo_session_continuity"],
                }
            )
            validate_turn(packet, live_tts=False, fallback_reason="dry-run-mode")
            assert_live_demo_response_style(packet["summary"]["final_response"], f"guided {topic} sequence")
        topic_responses = [packet["summary"]["final_response"] for packet in topic_packets]
        assert_sales_opening_response(topic_responses[0])
        assert_condition(
            len(topic_responses) == len(set(topic_responses)),
            f"Guided {topic} sequence must not replay responses: {topic_responses}",
        )
        for packet in topic_packets[1:]:
            response = packet["summary"]["final_response"]
            assert_condition(
                not response_reopens_focus_menu(response),
                f"Guided {topic} sequence reopened a focus menu: {response}",
            )
            assert_condition(
                packet["demo_session_continuity"]["applied"] is True,
                f"Guided {topic} sequence fell out of session policy: {packet['transcript']} -> {packet['demo_session_continuity']}",
            )
        if topic == "timing":
            assert_condition(
                topic_packets[1]["demo_session_continuity"].get("dialogue_focus") == "timing",
                f"Timing concern should resolve to timing focus: {topic_packets[1]['demo_session_continuity']}",
            )
        if topic == "features":
            assert_condition(
                topic_packets[1]["demo_session_continuity"].get("dialogue_focus") == "details",
                f"Feature questions should route to product details: {topic_packets[1]['demo_session_continuity']}",
            )

    callback_state = {"turns": []}
    callback_packets = []
    for callback_transcript in [
        "hey what's up",
        "I do not have time",
        "you should call me 10 a.m. tomorrow",
    ]:
        packet = build_turn_packet(
            transcript=callback_transcript,
            campaign_id="campaign-prod-005-b2b-software",
            stage="relevance-check",
            input_type="speech-final",
            silence_count=0,
            cases_path=DEFAULT_CASES_PATH,
            private_out=TMP_DIR,
            live_tts=False,
            force_key_missing=False,
            timeout_seconds=8.0,
            session_id="callback-scheduling-session",
            session_state=callback_state,
        )
        callback_packets.append(packet)
        callback_state["turns"].append(
            {
                "transcript": packet["transcript"],
                "summary": packet["summary"],
                "continuity": packet["demo_session_continuity"],
            }
        )
        validate_turn(packet, live_tts=False, fallback_reason="dry-run-mode")
        assert_live_demo_response_style(packet["summary"]["final_response"], "callback scheduling flow")

    assert_sales_opening_response(callback_packets[0]["summary"]["final_response"])
    no_time = callback_packets[1]
    no_time_continuity = no_time["demo_session_continuity"]
    no_time_semantics = no_time_continuity.get("contextual_buyer_semantics") or {}
    assert_condition(
        no_time_continuity["reason"] == "contextual_callback_scheduling_request",
        f"No-time boundary should ask for callback time through contextual semantics: {no_time_continuity}",
    )
    assert_condition(
        no_time_semantics.get("semantic") == "callback_scheduling_request",
        f"No-time boundary should classify as callback scheduling request: {no_time_semantics}",
    )
    assert_condition(
        no_time_semantics.get("action_id") == "request_callback_time",
        f"No-time boundary should request callback time: {no_time_semantics}",
    )
    assert_condition(
        no_time["summary"]["sales_difficulty"] == "callback-scheduling",
        f"No-time boundary should classify as callback request: {no_time['summary']}",
    )
    assert_condition(
        no_time["summary"]["next_action"] == "request-callback-time",
        f"No-time boundary should offer scheduling: {no_time['summary']}",
    )
    assert_condition(
        not response_reopens_focus_menu(no_time["summary"]["final_response"]),
        f"No-time boundary reopened a topic menu: {no_time['summary']['final_response']}",
    )
    assert_contains_any(no_time["summary"]["final_response"], {"time", "callback"}, "no-time callback request")

    callback_time = callback_packets[2]
    callback_time_continuity = callback_time["demo_session_continuity"]
    callback_time_semantics = callback_time_continuity.get("contextual_buyer_semantics") or {}
    assert_condition(
        callback_time_continuity["reason"] == "contextual_callback_time_confirmation",
        f"Callback time should be confirmed through contextual semantics: {callback_time_continuity}",
    )
    assert_condition(
        callback_time_semantics.get("semantic") == "callback_time_confirmation",
        f"Callback time should use callback-time semantics: {callback_time_semantics}",
    )
    assert_condition(
        callback_time_semantics.get("action_id") == "confirm_callback_and_end",
        f"Callback time should confirm callback and end: {callback_time_semantics}",
    )
    assert_condition(
        callback_time["summary"]["sales_difficulty"] == "scheduling-confirmation",
        f"Callback time should classify as scheduling confirmation: {callback_time['summary']}",
    )
    assert_condition(
        callback_time["summary"]["next_action"] == "confirm-scheduling",
        f"Callback time should confirm scheduling: {callback_time['summary']}",
    )
    assert_condition(
        callback_time["summary"]["call_control"] == "schedule-and-end",
        f"Callback time should schedule and end: {callback_time['summary']}",
    )
    assert_contains_any(callback_time["summary"]["final_response"], {"callback", "goodbye", "confirmed"}, "callback time confirmation")
    assert_condition(
        not response_reopens_focus_menu(callback_time["summary"]["final_response"]),
        f"Callback time confirmation reopened a topic menu: {callback_time['summary']['final_response']}",
    )

    seller_close_state = {"turns": []}
    seller_close_packets = []
    for seller_transcript in [
        "I want to talk about the price",
        "handoffs",
    ]:
        packet = build_turn_packet(
            transcript=seller_transcript,
            campaign_id="campaign-prod-005-b2b-software",
            stage="relevance-check",
            input_type="speech-final",
            silence_count=0,
            cases_path=DEFAULT_CASES_PATH,
            private_out=TMP_DIR,
            live_tts=False,
            force_key_missing=False,
            timeout_seconds=8.0,
            session_id="seller-guided-close-session",
            session_state=seller_close_state,
        )
        seller_close_packets.append(packet)
        seller_close_state["turns"].append(
            {
                "transcript": packet["transcript"],
                "summary": packet["summary"],
                "continuity": packet["demo_session_continuity"],
            }
        )
        validate_turn(packet, live_tts=False, fallback_reason="dry-run-mode")

    seller_close = seller_close_packets[1]
    assert_condition(
        seller_close["demo_session_continuity"]["reason"] == "seller_gap_selected_for_price",
        f"Named buyer gap should move into seller-led close progression: {seller_close['demo_session_continuity']}",
    )
    assert_contains_any(
        seller_close["summary"]["final_response"],
        {"handoff review", "short workflow review", "next step"},
        "seller-guided close progression",
    )
    assert_seller_led_next_move(seller_close["summary"]["final_response"], "seller-guided close progression")
    assert_condition(
        "book a demo" not in seller_close["summary"]["final_response"].lower(),
        f"Seller-guided close should not hard-close: {seller_close['summary']['final_response']}",
    )

    noisy_asr_state = {"turns": []}
    noisy_asr_transcripts = [
        "hey what's up",
        "it's about the",
        "yeah I want to talk about the price",
        "but what is the price star",
        "no I don't I'm not wondering about payment I'm just wondering what is the price of your product",
    ]
    noisy_asr_packets = []
    for noisy_transcript in noisy_asr_transcripts:
        packet = build_turn_packet(
            transcript=noisy_transcript,
            campaign_id="campaign-prod-005-b2b-software",
            stage="relevance-check",
            input_type="speech-final",
            silence_count=0,
            cases_path=DEFAULT_CASES_PATH,
            private_out=TMP_DIR,
            live_tts=False,
            force_key_missing=False,
            timeout_seconds=8.0,
            session_id="noisy-asr-session",
            session_state=noisy_asr_state,
        )
        noisy_asr_packets.append(packet)
        noisy_asr_state["turns"].append(
            {
                "transcript": packet["transcript"],
                "summary": packet["summary"],
                "continuity": packet["demo_session_continuity"],
            }
        )
        validate_turn(packet, live_tts=False, fallback_reason="dry-run-mode")
        assert_live_demo_response_style(packet["summary"]["final_response"], f"noisy ASR turn {len(noisy_asr_packets)}")
    assert_condition(
        "only caught part" in noisy_asr_packets[1]["summary"]["final_response"].lower(),
        f"Incomplete STT fragment should ask for a clean repeat: {noisy_asr_packets[1]['summary']['final_response']}",
    )
    assert_condition(
        "$29/month" in noisy_asr_packets[2]["summary"]["final_response"]
        and "$59/month" in noisy_asr_packets[2]["summary"]["final_response"],
        f"First clear price answer missing demo prices: {noisy_asr_packets[2]['summary']['final_response']}",
    )
    for price_packet in noisy_asr_packets[2:]:
        price_response = price_packet["summary"]["final_response"]
        assert_contains_any(price_response, {"$29/month", "$59/month", "growth", "starter", "routing", "handoff"}, "noisy ASR price sequence")
        assert_condition("specialist" not in price_response.lower(), f"Price answer should not hand off unnecessarily: {price_response}")
    assert_condition(
        "payment" not in noisy_asr_packets[4]["summary"]["final_response"].lower(),
        f"Payment negation should not make the answer talk about payment: {noisy_asr_packets[4]['summary']['final_response']}",
    )

    option_state = {"turns": []}
    option_prompt = build_turn_packet(
        transcript="I am not sure yet.",
        campaign_id="campaign-prod-005-b2b-software",
        stage="relevance-check",
        input_type="speech-final",
        silence_count=0,
        cases_path=DEFAULT_CASES_PATH,
        private_out=TMP_DIR / "private",
        live_tts=False,
        force_key_missing=False,
        timeout_seconds=8.0,
        session_id="option-session",
        session_state=option_state,
    )
    option_state["turns"].append({"transcript": option_prompt["transcript"], "summary": option_prompt["summary"]})
    option_answer = build_turn_packet(
        transcript="fit",
        campaign_id="campaign-prod-005-b2b-software",
        stage="relevance-check",
        input_type="speech-final",
        silence_count=0,
        cases_path=DEFAULT_CASES_PATH,
        private_out=TMP_DIR / "private",
        live_tts=False,
        force_key_missing=False,
        timeout_seconds=8.0,
        session_id="option-session",
        session_state=option_state,
    )
    assert_condition(option_answer["demo_session_continuity"]["applied"] is True, "Generic option prompt should accept a short fit answer.")
    assert_condition("fit" in option_answer["summary"]["final_response"].lower(), "Fit continuity response missing.")
    assert_condition("price, fit, timing" not in option_answer["summary"]["final_response"].lower(), "Fit answer should not repeat the generic option prompt.")
    assert_live_demo_response_style(option_answer["summary"]["final_response"], "short fit answer")
    validate_turn(option_answer, live_tts=False, fallback_reason="dry-run-mode")

    live_observed_state = {"turns": []}
    live_observed_transcripts = [
        "hey how's it going",
        "first of all let's start with the price",
        "my main concern is whether reviewing options is worth my time or not",
        "it's about whether a viewing options is worth my time",
    ]
    live_observed_packets = []
    for live_transcript in live_observed_transcripts:
        packet = build_turn_packet(
            transcript=live_transcript,
            campaign_id="campaign-prod-005-b2b-software",
            stage="relevance-check",
            input_type="speech-final",
            silence_count=0,
            cases_path=DEFAULT_CASES_PATH,
            private_out=TMP_DIR / "private",
            live_tts=False,
            force_key_missing=False,
            timeout_seconds=8.0,
            session_id="live-observed-session",
            session_state=live_observed_state,
        )
        live_observed_packets.append(packet)
        live_observed_state["turns"].append(
            {
                "transcript": packet["transcript"],
                "summary": packet["summary"],
                "continuity": packet["demo_session_continuity"],
            }
        )
        validate_turn(packet, live_tts=False, fallback_reason="dry-run-mode")
    assert_condition(
        live_observed_packets[1]["demo_session_continuity"]["reason"] == "focus_shift_to_price_from_qualification",
        "Observed price phrase should shift from the agent-led qualification opener into price.",
    )
    assert_condition(
        live_observed_packets[2]["demo_session_continuity"]["reason"] == "focus_shift_to_effort_from_price",
        "Observed worth-my-time phrase should shift from price to effort instead of repeating the price choice.",
    )
    assert_condition(
        live_observed_packets[3]["demo_session_continuity"]["dialogue_focus"] == "effort",
        "Observed worth-my-time follow-up should persist effort focus.",
    )
    assert_condition(
        live_observed_packets[3]["summary"]["final_response"] != live_observed_packets[2]["summary"]["final_response"],
        "Persisted effort focus should advance the response instead of replaying the same answer.",
    )
    for packet in live_observed_packets[1:]:
        assert_condition(
            "bigger concern" not in packet["summary"]["final_response"].lower(),
            "Observed live sequence must not repeat the price/terms/effort question.",
        )
        assert_live_demo_response_style(packet["summary"]["final_response"], "observed live sequence")

    live_followup_state = {"turns": []}
    live_followup_transcripts = [
        "hi how are you doing",
        "let's talk about the price First",
        "all right let's do that",
        "it's about the price",
        "can you just explain to me about",
        "I want to talk about the product details",
        "so what does the workflow include",
    ]
    live_followup_packets = []
    for live_transcript in live_followup_transcripts:
        packet = build_turn_packet(
            transcript=live_transcript,
            campaign_id="campaign-prod-005-b2b-software",
            stage="relevance-check",
            input_type="speech-final",
            silence_count=0,
            cases_path=DEFAULT_CASES_PATH,
            private_out=TMP_DIR / "private",
            live_tts=False,
            force_key_missing=False,
            timeout_seconds=8.0,
            session_id="live-followup-session",
            session_state=live_followup_state,
        )
        live_followup_packets.append(packet)
        live_followup_state["turns"].append(
            {
                "transcript": packet["transcript"],
                "summary": packet["summary"],
                "continuity": packet["demo_session_continuity"],
            }
        )
        validate_turn(packet, live_tts=False, fallback_reason="dry-run-mode")
    actual_followup_reasons = [
        packet["demo_session_continuity"]["reason"] for packet in live_followup_packets[1:]
    ]
    assert_condition(
        all(
            reason.startswith(
                (
                    "initial_price_focus_selected",
                    "explicit_price_focus_selected",
                    "focus_shift_to_price_from_qualification",
                    "resolved_price_focus",
                    "duplicate_response_prevented_with_price_progression",
                    "focus_shift_to_details_from_price",
                    "resolved_details_focus",
                    "duplicate_response_prevented_with_details_progression",
                    "campaign_depth_product_explanation_answered",
                    "campaign_depth_workflow_scope_answered",
                    "asr_fragment_repair",
                )
            )
            for reason in actual_followup_reasons
        ),
        f"Observed live follow-up sequence should stay inside resolved topics without strict old menu reasons: {actual_followup_reasons}",
    )
    live_followup_responses = [packet["summary"]["final_response"] for packet in live_followup_packets]
    assert_condition(
        len(live_followup_responses) == len(set(live_followup_responses)),
        f"Observed live follow-up sequence should not replay responses: {live_followup_responses}",
    )
    for packet in live_followup_packets[1:]:
        lowered_response = packet["summary"]["final_response"].lower()
        assert_condition("main question about price, fit, timing" not in lowered_response, "Resolved follow-up should not reopen the generic focus menu.")
        assert_condition("bigger concern" not in lowered_response, "Resolved follow-up should not reopen the price choice menu.")
        assert_live_demo_response_style(packet["summary"]["final_response"], "observed live follow-up")
    product_after_price = live_followup_packets[6]
    assert_condition(
        product_after_price["demo_session_continuity"]["reason"] == "campaign_depth_workflow_scope_answered",
        f"Explicit product detail should not be swallowed by price duplicate repair: {product_after_price['demo_session_continuity']}",
    )
    assert_contains_any(
        product_after_price["summary"]["final_response"],
        {"lead capture", "qualification", "routing", "handoff review"},
        "product detail after price",
    )

    live_fit_state = {"turns": []}
    live_fit_transcripts = [
        "hey how's it going",
        "let's talk about the fit",
        "so it's mostly about the situation we can talk about the price later on",
        "talk about fit if the fit is good",
        "I want to talk about whether this is relevant for my situation or not",
    ]
    live_fit_packets = []
    for live_transcript in live_fit_transcripts:
        packet = build_turn_packet(
            transcript=live_transcript,
            campaign_id="campaign-prod-005-b2b-software",
            stage="relevance-check",
            input_type="speech-final",
            silence_count=0,
            cases_path=DEFAULT_CASES_PATH,
            private_out=TMP_DIR / "private",
            live_tts=False,
            force_key_missing=False,
            timeout_seconds=8.0,
            session_id="live-fit-session",
            session_state=live_fit_state,
        )
        live_fit_packets.append(packet)
        live_fit_state["turns"].append(
            {
                "transcript": packet["transcript"],
                "summary": packet["summary"],
                "continuity": packet["demo_session_continuity"],
            }
        )
        validate_turn(packet, live_tts=False, fallback_reason="dry-run-mode")
    focus_menu_count = sum(1 for packet in live_fit_packets if response_reopens_focus_menu(packet["summary"]["final_response"]))
    assert_condition(focus_menu_count <= 1, f"Focus menu should appear at most once per session, got {focus_menu_count}.")
    for packet in live_fit_packets[1:]:
        assert_condition(
            packet["demo_session_continuity"]["applied"] is True,
            f"Fit follow-up should be handled by session dialogue policy: {packet['transcript']}",
        )
        assert_condition(
            packet["demo_session_continuity"].get("dialogue_focus") == "fit",
            f"Fit sequence should stay on fit, got {packet['demo_session_continuity']}",
        )
        assert_condition(
            not response_reopens_focus_menu(packet["summary"]["final_response"]),
            f"Fit follow-up reopened a menu: {packet['summary']['final_response']}",
        )
        assert_live_demo_response_style(packet["summary"]["final_response"], "observed fit follow-up")
    live_fit_responses = [packet["summary"]["final_response"] for packet in live_fit_packets]
    assert_condition(
        len(live_fit_responses) == len(set(live_fit_responses)),
        f"Live fit sequence should not replay the same answer: {live_fit_responses}",
    )

    campaign_depth_cases = [
        {
            "transcript": "What does your product actually do?",
            "expected": {"routes leads", "lead capture", "handoff", "follow-up"},
            "forbid_specialist": True,
            "require_seller_led_next_move": True,
            "context": "product explanation",
        },
        {
            "transcript": "Why would I use this instead of tracking leads manually?",
            "expected": {"manual", "missed", "handoff", "follow-up", "wrong person"},
            "forbid_specialist": True,
            "forbid_leading_echo": ("manual tracking", "tracking leads manually"),
            "require_seller_led_next_move": True,
            "context": "manual tracking objection",
        },
        {
            "transcript": "What do I get for fifty nine dollars?",
            "expected": {"priority routing", "reminders", "handoff review"},
            "forbid_specialist": True,
            "forbid_customer_price_plan_echo": True,
            "forbid_leading_echo": ("growth", "$59", "59 dollars", "fifty nine"),
            "require_seller_led_next_move": True,
            "context": "growth plan value",
        },
        {
            "transcript": "What is included in the $59 version?",
            "expected": {"priority routing", "reminders", "handoff review"},
            "forbid_specialist": True,
            "forbid_customer_price_plan_echo": True,
            "forbid_leading_echo": ("growth", "$59", "59 dollars", "fifty nine"),
            "require_seller_led_next_move": True,
            "context": "59 version included value",
        },
        {
            "transcript": "Tell me about the Growth plan value.",
            "expected": {"priority routing", "reminders", "handoff review"},
            "forbid_specialist": True,
            "forbid_customer_price_plan_echo": True,
            "forbid_leading_echo": ("growth", "growth plan", "the growth"),
            "require_seller_led_next_move": True,
            "context": "growth plan named value",
        },
        {
            "transcript": "Is this worth it for a small team?",
            "expected": {"small team", "starter", "missed"},
            "forbid_specialist": True,
            "forbid_leading_echo": ("for a small team", "small team"),
            "require_seller_led_next_move": True,
            "context": "small team fit",
        },
        {
            "transcript": "Do I need to talk to a specialist?",
            "expected": {"not for basics", "price", "fit", "workflow"},
            "forbid_specialist": True,
            "context": "unnecessary handoff challenge",
        },
        {
            "transcript": "Does it integrate with Salesforce?",
            "expected": {"salesforce", "exact setup", "verify"},
            "forbid_specialist": False,
            "forbid_leading_echo": ("salesforce", "it integrates", "yes"),
            "context": "integration boundary",
        },
        {
            "transcript": "Are you SOC 2 certified?",
            "expected": {"cannot claim", "security", "verified"},
            "forbid_specialist": False,
            "forbid_leading_echo": ("soc 2", "yes", "security"),
            "context": "security boundary",
        },
        {
            "transcript": "What is included in the workflow?",
            "expected": {"lead capture", "routing", "reminders", "handoff review"},
            "forbid_specialist": True,
            "forbid_leading_echo": ("the workflow", "workflow"),
            "require_seller_led_next_move": True,
            "context": "workflow included value",
        },
    ]
    campaign_depth_packets = []
    for case in campaign_depth_cases:
        packet = build_turn_packet(
            transcript=case["transcript"],
            campaign_id="campaign-prod-005-b2b-software",
            stage="relevance-check",
            input_type="speech-final",
            silence_count=0,
            cases_path=DEFAULT_CASES_PATH,
            private_out=TMP_DIR / "private",
            live_tts=False,
            force_key_missing=False,
            timeout_seconds=8.0,
            session_id=f"campaign-depth-{case['context'].replace(' ', '-')}",
            session_state={"turns": []},
        )
        campaign_depth_packets.append(packet)
        validate_turn(packet, live_tts=False, fallback_reason="dry-run-mode")
        response = packet["summary"]["final_response"]
        assert_contains_any(response, case["expected"], case["context"])
        assert_no_campaign_depth_regressions(response, case["context"])
        assert_live_demo_response_style(response, case["context"])
        assert_browser_fallback_text_clean(
            packet["summary"].get("browser_fallback_speech_text", ""),
            f"{case['context']} browser fallback",
        )
        if case.get("forbid_leading_echo"):
            assert_no_leading_customer_echo(response, case["forbid_leading_echo"], case["context"])
            assert_no_leading_customer_echo(
                packet["summary"].get("browser_fallback_speech_text", ""),
                case["forbid_leading_echo"],
                f"{case['context']} browser fallback",
            )
        if case.get("forbid_customer_price_plan_echo"):
            assert_no_customer_price_plan_echo(response, case["context"])
            assert_no_customer_price_plan_echo(
                packet["summary"].get("browser_fallback_speech_text", ""),
                f"{case['context']} browser fallback",
            )
        if case.get("require_seller_led_next_move"):
            assert_seller_led_next_move(response, case["context"])
            assert_seller_led_next_move(
                packet["summary"].get("browser_fallback_speech_text", ""),
                f"{case['context']} browser fallback",
            )
        if case["forbid_specialist"]:
            assert_condition(
                "specialist" not in response.lower(),
                f"{case['context']} should not hand off basic campaign questions: {response}",
            )

    serialized = html + json.dumps(metadata) + json.dumps(dry_packet) + json.dumps(forced_packet) + json.dumps(runtime_upgrade_packet) + json.dumps(second) + json.dumps(third) + json.dumps(option_answer) + json.dumps(live_observed_packets) + json.dumps(live_followup_packets) + json.dumps(live_fit_packets) + json.dumps(campaign_depth_packets)
    assert_no_secret_patterns(serialized)
    print("LIVE-DEMO-001 agent voice call validation passed.")


if __name__ == "__main__":
    main()
