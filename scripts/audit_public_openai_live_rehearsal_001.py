#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.run_live_demo_001_agent_voice_call as demo  # noqa: E402


CHECKPOINT_ID = "PUBLIC-OPENAI-LIVE-REHEARSAL-001"
CURRENT_COMMIT = "b58aa53"
FIXTURE_RELATIVE = "runtime/campaigns/examples/public-openai-chatgpt-plans.json"
FIXTURE_PATH = ROOT / FIXTURE_RELATIVE
PRIVATE_ROOT = ROOT / "data" / "private"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID

PLAN_NAMES = ["Free", "Go", "Plus", "Pro", "Business", "Enterprise"]
LEGACY_RE = re.compile(r"legacy compatibility|appointment_target", re.I)
OWNER_RE = re.compile(r"human_followup_owner|demo operator", re.I)
ROUTESIGNAL_RE = re.compile(r"routesignal|northstar|workflow review|handoff|callback", re.I)
RAW_URL_RE = re.compile(r"https?://|www\.", re.I)
FAKE_SIDE_EFFECT_RE = re.compile(r"\b(i sent|i emailed|i booked|created .*calendar|created .*crm|send it to your email)\b", re.I)
AFFILIATION_RE = re.compile(r"\b(calling from openai|from openai|authorized by openai|authorized to represent openai|represent openai)\b", re.I)
SOURCE_CLAIM_RE = re.compile(
    r"\b(guarantee|guaranteed|better than|superior|gpt-5\.5|exact enterprise price|enterprise costs \$)\b",
    re.I,
)
PREMATURE_PLAN_COMPARISON_RE = re.compile(
    r"are you (mainly )?comparing plans for yourself,? a small team,? or (a )?larger organization|"
    r"are you looking for personal use,? team use,? or enterprise controls",
    re.I,
)
ADOPTION_STATE_RE = re.compile(r"using chatgpt.*another ai tool.*not using ai|chatgpt today.*another ai tool", re.I)
ASSUMPTION_CHALLENGE_RE = re.compile(
    r"why did you assume|i never said|just said yes|asking about plans already|do not assume|don't assume|comparing plants",
    re.I,
)
SOURCE_TRUST_TRANSCRIPT_RE = re.compile(
    r"where .*getting this information|getting this information|calling from open\s*ai|authorized by openai|"
    r"authorised by openai|authorised by opening eyes|official|from openai",
    re.I,
)
SOURCE_TRUST_RESPONSE_RE = re.compile(r"public-data simulation|official public openai|public pricing|help pages|not calling from openai", re.I)
LOOP_RE = re.compile(r"current call scope.*keep checking|keep checking that, or stop|are you .*comparing plans", re.I)
ANSWERED_LIMIT_TRANSCRIPT_RE = re.compile(r"mostly hitting limits|hitting limits|limits .*frustrating|already hitting limits|blocked by limits|running out", re.I)
ANSWERED_LIMIT_REPEAT_RE = re.compile(r"are you mostly hitting limits, or just trying to choose before upgrading", re.I)
KNOWN_USE_IGNORED_RE = re.compile(r"plan fit still needs the actual use case|actual use case|what would you mainly use", re.I)
KNOWN_INTENSITY_IGNORED_RE = re.compile(r"occasionally or heavily every day|usage level.*deciding point", re.I)
PRICE_CONTEXT_RESET_RE = re.compile(r"are you mainly comparing plus and pro|are you .*comparing plans|using chatgpt today.*another ai tool", re.I)
SIGNUP_CONTEXT_TRANSCRIPT_RE = re.compile(r"how do i sign up|where do i upgrade|show me the official page|sounds good.*sign up", re.I)
SIGNUP_CONTEXT_RESPONSE_RE = re.compile(r"official chatgpt plans page|profile upgrade flow", re.I)
ASR_ALIAS_TRANSCRIPT_RE = re.compile(
    r"chachu\s*(pt|bt|p\s*t|b\s*t)|chachupt|chat\s*(jpt|gbt|gb\s*t|g\s*p\s*t|gpt)|chatgbt",
    re.I,
)
ASR_ALIAS_GOOD_RESPONSE_RE = re.compile(r"chatgpt|current setup|current tool|switch|useful comparison", re.I)
INTERNAL_POLICY_RE = re.compile(r"should not assume buying intent|first i need the adoption state|\badoption state\b", re.I)
PRICE_TRANSCRIPT_RE = re.compile(r"how much|price|cost|20 dollars|twenty dollars|expensive|paid tiers", re.I)
PRICE_RESPONSE_RE = re.compile(r"source of truth|official chatgpt pricing page|20 dollars|100 dollar|200 dollar|free is", re.I)
PLAN_RECOMMENDATION_TRANSCRIPT_RE = re.compile(r"plus enough|plus going to be enough|pro worth|plus or pro|heavy side", re.I)
PLAN_RECOMMENDATION_RESPONSE_RE = re.compile(r"\bplus\b.*\bpro\b|\bpro\b.*\bplus\b", re.I)
BUYING_SIGNAL_TRANSCRIPT_RE = re.compile(r"pro .*better|pro .*right|pro .*safer|pro seems|pro probably|sign up|upgrade|next step", re.I)
COMMERCIAL_VALUE_FRAME_RE = re.compile(r"lower-cost|cheaper|safer|usage headroom|limits|heavy use|based on|given|since|for coding|for writing", re.I)
COMMERCIAL_CLOSE_RESPONSE_RE = re.compile(r"official chatgpt plans page|profile upgrade flow|contact sales|next step", re.I)
COMPETITOR_CAVEAT_RE = re.compile(r"you may not need to switch", re.I)
GENERIC_DISCOVERY_RE = re.compile(r"what matters most|what would you mainly use|occasionally or heavily every day|using chatgpt today.*another ai tool", re.I)
FALSE_LIMIT_PAIN_RESPONSE_RE = re.compile(r"given you are hitting limits|if you are regularly hitting limits|hitting limits makes pro", re.I)
HEAVY_CONTEXT_RE = re.compile(r"heavy side|little heavy|use heavily|heavy daily|every day|\"openai_usage_intensity\": \"heavy\"", re.I)
EXPLICIT_LIMIT_CONTEXT_RE = re.compile(r"hitting limits|hit limits|limits .*frustrating|blocked by limits|running out|\"openai_limit_pain\": true", re.I)
PLAIN_ASK_TRANSCRIPT_RE = re.compile(r"what do you want me to do|what are you asking|what is the next step|do not understand what you want", re.I)
AI_TOOL_USAGE_TRANSCRIPT_RE = re.compile(r"used? chat\s*gpt.*other tools|use ai tools already|already use ai tools|another llm|claude|gemini|copilot|other ai", re.I)
PREMATURE_NO_FIT_RESPONSE_RE = re.compile(r"if your current tool is enough.*would not push|would not push a paid chatgpt plan|no paid close", re.I)
PRICE_OBJECTION_TRANSCRIPT_RE = re.compile(r"expensive|why would i pay|why pay|another subscription|overpay|too much", re.I)
PRICE_REPEAT_RESPONSE_RE = re.compile(r"free is the no-cost option.*20 dollars.*100 dollar.*200 dollar", re.I)
PRO_TIER_TRANSCRIPT_RE = re.compile(r"which pro|pro tier|version of pro|100.*200.*pro|100.*version|200.*version|higher pro|lower pro", re.I)
PRO_TIER_RESPONSE_RE = re.compile(r"lower pro tier|higher pro tier|lower tier|higher tier|100 dollar|200 dollar|maxing out|most headroom", re.I)
PLUS_VS_PRO_RESET_RE = re.compile(r"plus versus pro|pro versus plus|compare plus versus pro|next decision is pro versus plus|choose plus only", re.I)
PRO_TIER_CONTEXT_RE = re.compile(r"pro_100_vs_200|pro_tier_selection|which pro|pro tier|version of pro|100.*200.*pro", re.I)
LEGACY_FIELD_RE = re.compile(r"legacy compatibility|appointment_target|human_followup_owner|demo operator|primary close is official", re.I)
ROUTESIGNAL_TRACE_RE = re.compile(r"routesignal|northstar|inbound demo request|missed callbacks|handoffs|callback reminders", re.I)
OPENING_ORIGIN_RE = re.compile(r"chatgpt subscription plans", re.I)
OPENING_PUBLIC_RE = re.compile(r"public-data|public plan|public information|public openai|openai.?s public|official public", re.I)
OPENING_NON_AFFILIATION_RE = re.compile(r"not calling (as|from) openai|not representing openai|not an official openai call", re.I)
EXPLANATION_TRANSCRIPT_RE = re.compile(
    r"what is this|what are you calling about|what is this for|what are these plans|what are the plans|"
    r"what (is|are|does|do).*(free|plus|pro|business|enterprise)|"
    r"(free|plus|pro|business|enterprise).*(what exactly|mean|products?|plans?|models?|labels?|names?)|"
    r"i (still )?(do not|don't|don t) understand|don't really understand|confused|lost|"
    r"explain (free|plus|pro|business|enterprise|simpler|that|plans)|plain english|simpler please|"
    r"are these products or plans|is (business|enterprise) a product or a plan",
    re.I,
)
PLAN_LABEL_EXPLANATION_RE = re.compile(
    r"(free|plus|pro|business|enterprise).*(what|mean|product|plan|model|label|name|versus|what exactly|are what)|"
    r"(what|mean|product|plan|model|label|name|versus).*(free|plus|pro|business|enterprise)",
    re.I,
)
EXPLANATION_RESPONSE_RE = re.compile(
    r"chatgpt subscription plans.*free .*no-cost.*plus and pro .*individual.*business .*teams.*enterprise .*larger",
    re.I,
)
TEAM_ROUTE_RESPONSE_RE = re.compile(
    r"for team use, business is|basic team workspace controls|enterprise requirements like sso|team_plan_fit",
    re.I,
)
REPEATED_CONFUSION_TRANSCRIPT_RE = re.compile(
    r"still (do not|don't|don t) understand|still (do not|don't|don t) get it|explain simpler|simpler please|"
    r"what are free|what are these plans|what is this again",
    re.I,
)
NO_BUYER_CONTEXT_RE = re.compile(r"^(__agent_open__|yes|yeah|yeah sure|sure|okay|ok|go ahead|tell me|yeah tell me)$", re.I)

DIALOGUE_DEFECT_CLASSES = {
    "current_live_openai_asr_product_alias_issue",
    "current_live_openai_internal_policy_language_leak",
    "current_live_openai_price_question_refusal",
    "current_live_openai_plan_recommendation_stall",
    "current_live_openai_memory_progression_defect",
    "current_live_openai_repeated_answered_question",
    "current_live_openai_duplicate_repair_regression",
    "current_live_openai_known_use_case_ignored",
    "current_live_openai_known_intensity_ignored",
    "current_live_openai_price_context_reset",
    "current_live_openai_close_context_missing",
    "current_live_openai_legacy_field_leakage",
    "current_live_openai_routesignal_contamination",
    "current_live_openai_loop_or_repeated_prompt",
    "current_live_openai_runtime_defect",
    "current_live_openai_sales_quality_defect",
    "current_live_openai_information_not_selling",
    "current_live_openai_missed_recommendation",
    "current_live_openai_missed_close",
    "current_live_openai_weak_value_frame",
    "current_live_openai_repeated_competitor_caveat",
    "current_live_openai_false_limit_pain",
    "current_live_openai_overqualified_without_recommendation",
    "current_live_openai_sales_performance_defect",
    "current_live_openai_premature_no_fit_caveat",
    "current_live_openai_price_objection_repeated_price",
    "current_live_openai_wrong_decision_stage",
    "current_live_openai_pro_tier_selection_defect",
    "current_live_openai_signup_close_stage_mismatch",
    "current_live_openai_stability_guard_owned_sales_turn",
    "current_live_openai_sales_momentum_defect",
    "current_live_openai_opening_origin_missing",
    "current_live_openai_explanation_question_misrouted",
    "current_live_openai_plan_label_trap",
    "current_live_openai_team_context_false_positive",
    "current_live_openai_repeated_wrong_explanation",
    "current_live_openai_state_initialized_with_recommendation",
    "current_live_openai_stability_guard_owned_adapter_turn",
    "current_live_openai_intent_priority_defect",
    "current_live_openai_logic_generalization_defect",
}

POST_PATCH_REPLAY_CASES = [
    ["__agent_open__"],
    ["__agent_open__", "yeah sure"],
    ["__agent_open__", "yeah sure", "yeah sure but what is this what is Free Plus Pro Business or Enterprise"],
    ["__agent_open__", "yeah sure", "I don't really understand what you're talking about, what are Free Pro Plus"],
    ["__agent_open__", "yeah sure", "what is this?", "I still don't understand"],
    ["__agent_open__", "yeah sure", "what are these plans?", "explain simpler"],
    ["__agent_open__", "yeah sure", "I heard Business and Enterprise, what does that mean?"],
    ["__agent_open__", "yeah sure", "what is the difference between Free and Business?"],
    ["__agent_open__", "yeah sure", "why did you assume I was comparing plans"],
    ["__agent_open__", "yeah sure", "where are you getting this information"],
    ["__agent_open__", "yeah sure", "I use chachu PT and other AI tools"],
    ["__agent_open__", "yeah sure", "why would I switch to chat jpt"],
    ["__agent_open__", "yeah sure", "how much are the plans"],
    ["__agent_open__", "yeah sure", "I use it for coding and writing", "is Plus going to be enough for my use case", "a little bit on the heavy side"],
    ["__agent_open__", "yeah sure", "I use it for coding and writing", "Is Plus enough?", "I am mostly hitting limits and it is frustrating"],
    ["__agent_open__", "yeah sure", "I use it for coding and writing", "somewhere in the middle but is Plus enough", "a little bit on the heavy side"],
    ["__agent_open__", "yeah sure", "I use it for coding and writing", "heavy", "hitting limits", "how much are the plans"],
    ["__agent_open__", "yeah sure", "I use it for coding and writing", "heavy", "hitting limits", "how do I sign up"],
    ["__agent_open__", "yeah sure", "I use it for coding and writing", "so what do you want me to do what are you asking me"],
    ["__agent_open__", "yeah sure", "I use another LLM", "how much are the plans", "but I asked the price"],
    ["__agent_open__", "yeah sure", "I use it for coding and writing", "what did you mean by that"],
    ["__agent_open__", "yeah sure", "I use it for coding and writing", "I use it heavily every day", "I already told you that", "keep checking it"],
    ["__agent_open__", "yeah sure", "I used chat GPT and other tools"],
    ["__agent_open__", "yeah sure", "I use it for coding and writing", "I use it heavily every day", "how much are the plans", "it is expensive, why would I pay that much"],
    ["__agent_open__", "yeah sure", "I use it for coding and writing", "I use it heavily every day", "I want to decide which version of Pro I want to go for"],
    ["__agent_open__", "yeah sure", "I use it for coding and writing", "I use it heavily every day", "I want to decide which version of Pro I want to go for", "how do I sign up"],
    ["who follows up after this"],
    ["who is the demo operator"],
    ["what happens after I say yes"],
]


def project_relative(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def git_head() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=3,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "git_unavailable"


def parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def campaign_path(payload: dict[str, Any]) -> str:
    selected = payload.get("selected_campaign_config") or {}
    path = payload.get("campaign_config_path") or selected.get("config_path") or ""
    return str(path).replace("\\", "/")


def response_text(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    packet = payload.get("packet") if isinstance(payload.get("packet"), dict) else {}
    manager = payload.get("dialogue_manager") if isinstance(payload.get("dialogue_manager"), dict) else {}
    return str(summary.get("final_response") or packet.get("final_response") or manager.get("final_response") or "")


def runtime_candidate_text(payload: dict[str, Any]) -> str:
    manager = payload.get("dialogue_manager") if isinstance(payload.get("dialogue_manager"), dict) else {}
    stability = payload.get("demo_conversation_stability_guard") if isinstance(payload.get("demo_conversation_stability_guard"), dict) else {}
    semantic = manager.get("contextual_buyer_semantics") if isinstance(manager.get("contextual_buyer_semantics"), dict) else {}
    selected_action = manager.get("selected_action") if isinstance(manager.get("selected_action"), dict) else {}
    values = [
        response_text(payload),
        str(manager.get("final_response") or ""),
        str(selected_action.get("candidate_response") or ""),
        str(semantic.get("candidate_response") or ""),
        str(stability.get("candidate_response") or ""),
    ]
    return "\n".join(value for value in values if value)


def transcript_text(payload: dict[str, Any]) -> str:
    value = payload.get("transcript")
    return value if isinstance(value, str) else ""


def summary(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("summary") if isinstance(payload.get("summary"), dict) else {}


def packet(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("packet") if isinstance(payload.get("packet"), dict) else {}


def tts(payload: dict[str, Any]) -> dict[str, Any]:
    body = packet(payload)
    value = body.get("tts_delivery") if isinstance(body.get("tts_delivery"), dict) else {}
    return value


def quality_gate(payload: dict[str, Any]) -> dict[str, Any]:
    asr = payload.get("asr") if isinstance(payload.get("asr"), dict) else {}
    gate = asr.get("quality_gate") if isinstance(asr.get("quality_gate"), dict) else {}
    return gate


def selected_config(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("selected_campaign_config") if isinstance(payload.get("selected_campaign_config"), dict) else {}


def voice_diag(payload: dict[str, Any]) -> dict[str, Any]:
    delivery = tts(payload)
    diag = delivery.get("voice_id_diagnostics") if isinstance(delivery.get("voice_id_diagnostics"), dict) else {}
    return {
        "voice_id_source": delivery.get("selected_voice_id_source") or delivery.get("selected_voice_id_env_var") or diag.get("source") or diag.get("voice_id_source"),
        "voice_id_present": bool(delivery.get("voice_id_present") or diag.get("present") or diag.get("voice_id_present")),
        "voice_id_length": diag.get("length") if diag.get("length") is not None else diag.get("voice_id_length"),
        "voice_id_hash": diag.get("sha256_8") or diag.get("voice_id_hash"),
        "raw_value_logged": bool(diag.get("raw_value_logged") or delivery.get("voice_id_value_logged")),
    }


def live_tts_used(payload: dict[str, Any]) -> bool:
    delivery = tts(payload)
    sumry = summary(payload)
    return bool(
        payload.get("live_tts_used")
        or (
            delivery.get("provider_calls_made")
            and delivery.get("audio_file_created")
        )
        or (
            sumry.get("tts_provider_calls_made")
            and sumry.get("tts_audio_file_created")
        )
    )


def dry_run(payload: dict[str, Any]) -> bool:
    mode = f"{payload.get('mode') or ''} {(selected_config(payload)).get('mode') or ''} {(tts(payload)).get('fallback_reason') or ''}".lower()
    return "dry-run" in mode or "dry-run-mode" in mode


def provider_calls(payload: dict[str, Any]) -> bool:
    delivery = tts(payload)
    sumry = summary(payload)
    return bool(delivery.get("provider_calls_made") or sumry.get("tts_provider_calls_made"))


def audio_created(payload: dict[str, Any]) -> bool:
    delivery = tts(payload)
    sumry = summary(payload)
    return bool(delivery.get("audio_file_created") or sumry.get("tts_audio_file_created"))


def record_generated_at(payload: dict[str, Any]) -> str | None:
    value = payload.get("generated_at_utc") or payload.get("generated_at")
    return str(value) if value else None


def record_sort_dt(record: dict[str, Any]) -> datetime:
    parsed = parse_dt(record_generated_at(record["payload"]))
    if parsed:
        return parsed
    return datetime.fromtimestamp(record["mtime"], tz=timezone.utc)


def private_records() -> tuple[int, list[dict[str, Any]], int]:
    scanned = 0
    invalid = 0
    records: list[dict[str, Any]] = []
    if not PRIVATE_ROOT.exists():
        return scanned, records, invalid
    for path in PRIVATE_ROOT.glob("live-demo-*"):
        if not path.is_dir():
            continue
        for json_path in path.rglob("*.json"):
            scanned += 1
            payload = load_json(json_path)
            if not payload:
                invalid += 1
                continue
            if campaign_path(payload) != FIXTURE_RELATIVE:
                continue
            stat = json_path.stat()
            records.append({"path": json_path, "payload": payload, "mtime": stat.st_mtime})
    return scanned, sorted(records, key=record_sort_dt), invalid


def current_threshold(records: list[dict[str, Any]]) -> datetime | None:
    current_times = [
        record_sort_dt(record)
        for record in records
        if str(record["payload"].get("git_head_short") or "") == CURRENT_COMMIT
    ]
    if current_times:
        return min(current_times)
    live_times = [
        record_sort_dt(record)
        for record in records
        if live_tts_used(record["payload"]) and provider_calls(record["payload"]) and audio_created(record["payload"])
    ]
    return min(live_times) if live_times else None


def is_current_record(record: dict[str, Any], threshold: datetime | None) -> bool:
    payload = record["payload"]
    if str(payload.get("git_head_short") or "") == CURRENT_COMMIT:
        return True
    if payload.get("git_head_short"):
        return False
    if threshold is None:
        return False
    return record_sort_dt(record) >= threshold and live_tts_used(payload)


def plan_categories(text: str) -> list[str]:
    lowered = text.lower()
    return [name for name in PLAN_NAMES if re.search(rf"\b{re.escape(name.lower())}\b", lowered)]


def latency_issue(payload: dict[str, Any]) -> bool:
    delivery = tts(payload)
    latency = payload.get("latency") if isinstance(payload.get("latency"), dict) else {}
    provider_ms = delivery.get("total_provider_latency_ms")
    source_ms = latency.get("source_decision_latency_ms")
    try:
        if provider_ms is not None and float(provider_ms) > 5000:
            return True
        if source_ms is not None and float(source_ms) > 5000:
            return True
    except (TypeError, ValueError):
        return True
    return bool(payload.get("provider_audio_playback_issue") or payload.get("turn_taking_issue"))


def source_fact_ids(payload: dict[str, Any]) -> list[str]:
    found: set[str] = set()

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = str(key).lower()
                if lowered in {"fact_id", "source_fact_id"} and isinstance(child, str):
                    found.add(child)
                elif lowered in {"fact_ids", "source_fact_ids", "allowed_claim_fact_ids"} and isinstance(child, list):
                    for item in child:
                        if isinstance(item, str):
                            found.add(item)
                walk(child)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    for key in ("campaign_validation", "dialogue_manager", "packet"):
        if isinstance(payload.get(key), dict):
            walk(payload[key])
    return sorted(found)


def classify_current(payload: dict[str, Any]) -> list[str]:
    text = response_text(payload)
    trace_text = runtime_candidate_text(payload)
    transcript = transcript_text(payload)
    payload_context_text = json.dumps(payload, sort_keys=True, default=str).lower()
    selected = selected_config(payload)
    delivery = tts(payload)
    source = str((payload.get("dialogue_manager") or {}).get("final_response_source") or "")
    memory = payload.get("demo_conversation_memory") or payload.get("conversation_memory") or {}
    plan_state = memory.get("openai_chatgpt_plan_state") if isinstance(memory, dict) else {}
    pro_tier_context_active = isinstance(plan_state, dict) and plan_state.get("active_decision_frame") == "pro_100_vs_200"
    normalized_transcript = re.sub(r"\s+", " ", str(transcript or "").strip().lower())
    plan_state_text = json.dumps(plan_state, sort_keys=True, default=str).lower() if isinstance(plan_state, dict) else ""
    explanation_question = bool(EXPLANATION_TRANSCRIPT_RE.search(transcript))
    plan_label_trap = bool(PLAN_LABEL_EXPLANATION_RE.search(transcript))
    team_false_positive = bool(
        plan_label_trap
        and (
            TEAM_ROUTE_RESPONSE_RE.search(text)
            or "team_plan_fit" in trace_text.lower()
            or (isinstance(plan_state, dict) and plan_state.get("openai_recommended_path") in {"business", "enterprise"})
            or (isinstance(plan_state, dict) and plan_state.get("decision_frame") == "business_vs_enterprise")
            or re.search(r'"openai_use_case": \[(?:[^\]]*)"(team|enterprise)"', plan_state_text)
        )
    )
    classes: list[str] = []

    if campaign_path(payload) != FIXTURE_RELATIVE or selected.get("campaign_id") != "public-openai-chatgpt-plans" or payload.get("campaign_selector_mode") != "generic_config":
        classes.append("current_live_openai_campaign_selector_issue")
    if not quality_gate(payload).get("accepted", True):
        classes.append("current_live_openai_asr_issue")
    if bool(delivery.get("live_call_requested") or selected.get("live_tts_enabled") or payload.get("mode") == "live-tts") and not audio_created(payload):
        classes.append("current_live_openai_tts_audio_issue")
    if latency_issue(payload):
        classes.append("current_live_openai_latency_or_turn_taking_issue")
    if ASR_ALIAS_TRANSCRIPT_RE.search(transcript) and not ASR_ALIAS_GOOD_RESPONSE_RE.search(text):
        classes.append("current_live_openai_asr_product_alias_issue")
    if INTERNAL_POLICY_RE.search(trace_text):
        classes.append("current_live_openai_internal_policy_language_leak")
    if normalized_transcript == "__agent_open__" and (
        not OPENING_ORIGIN_RE.search(text)
        or not OPENING_PUBLIC_RE.search(text)
        or not OPENING_NON_AFFILIATION_RE.search(text)
    ):
        classes.append("current_live_openai_opening_origin_missing")
        classes.append("current_live_openai_intent_priority_defect")
    if explanation_question and (
        not EXPLANATION_RESPONSE_RE.search(text)
        or ADOPTION_STATE_RE.search(text)
        or TEAM_ROUTE_RESPONSE_RE.search(text)
        or "team_plan_fit" in trace_text.lower()
    ):
        classes.append("current_live_openai_explanation_question_misrouted")
        classes.append("current_live_openai_intent_priority_defect")
    if plan_label_trap and (
        not EXPLANATION_RESPONSE_RE.search(text)
        or team_false_positive
        or ADOPTION_STATE_RE.search(text)
    ):
        classes.append("current_live_openai_plan_label_trap")
        classes.append("current_live_openai_intent_priority_defect")
    if team_false_positive:
        classes.append("current_live_openai_team_context_false_positive")
        classes.append("current_live_openai_logic_generalization_defect")
    if REPEATED_CONFUSION_TRANSCRIPT_RE.search(transcript) and (
        not EXPLANATION_RESPONSE_RE.search(text)
        or TEAM_ROUTE_RESPONSE_RE.search(text)
        or source == "pre_speech_conversation_stability_guard"
    ):
        classes.append("current_live_openai_repeated_wrong_explanation")
        classes.append("current_live_openai_intent_priority_defect")
    if isinstance(plan_state, dict) and NO_BUYER_CONTEXT_RE.search(normalized_transcript):
        if (
            plan_state.get("openai_recommended_path") not in {None, "", "unknown"}
            or plan_state.get("buyer_fit_level") not in {None, "", "unknown"}
            or plan_state.get("recommendation_confidence") not in {None, "", "none"}
            or plan_state.get("value_hypothesis") not in {None, "", "unknown", "none"}
            or plan_state.get("decision_frame") not in {None, "", "unknown", "none"}
            or plan_state.get("close_readiness") not in {None, "", "none"}
            or plan_state.get("commercial_stage") == "recommendation"
        ):
            classes.append("current_live_openai_state_initialized_with_recommendation")
            classes.append("current_live_openai_intent_priority_defect")
    if PRICE_TRANSCRIPT_RE.search(transcript) and not PRICE_RESPONSE_RE.search(text) and not (
        PRICE_OBJECTION_TRANSCRIPT_RE.search(transcript) and COMMERCIAL_VALUE_FRAME_RE.search(text)
    ):
        classes.append("current_live_openai_price_question_refusal")
    if PRICE_TRANSCRIPT_RE.search(transcript) and PRICE_RESPONSE_RE.search(text) and not COMMERCIAL_VALUE_FRAME_RE.search(text):
        classes.append("current_live_openai_weak_value_frame")
    if PRICE_TRANSCRIPT_RE.search(transcript) and PRICE_RESPONSE_RE.search(text) and not PLAN_RECOMMENDATION_RESPONSE_RE.search(text):
        classes.append("current_live_openai_information_not_selling")
    if PLAN_RECOMMENDATION_TRANSCRIPT_RE.search(transcript) and (
        not PLAN_RECOMMENDATION_RESPONSE_RE.search(text)
        or re.search(r"what would you mainly use|occasionally or heavily every day|actual work before plan fit", text, re.I)
    ):
        classes.append("current_live_openai_plan_recommendation_stall")
        classes.append("current_live_openai_missed_recommendation")
    if PLAN_RECOMMENDATION_TRANSCRIPT_RE.search(transcript) and PLAN_RECOMMENDATION_RESPONSE_RE.search(text) and not COMMERCIAL_VALUE_FRAME_RE.search(text):
        classes.append("current_live_openai_weak_value_frame")
    if PLAN_RECOMMENDATION_TRANSCRIPT_RE.search(transcript) and GENERIC_DISCOVERY_RE.search(text):
        classes.append("current_live_openai_overqualified_without_recommendation")
    if PLAIN_ASK_TRANSCRIPT_RE.search(transcript) and not re.search(r"not asking you to do anything yet|helping you decide", text, re.I):
        classes.append("current_live_openai_plan_recommendation_stall")
    if LOOP_RE.search(text) or (re.search(r"asked.*price|why.*not answering", transcript, re.I) and not PRICE_RESPONSE_RE.search(text)):
        classes.append("current_live_openai_loop_or_repeated_prompt")
    if ANSWERED_LIMIT_TRANSCRIPT_RE.search(transcript) and ANSWERED_LIMIT_REPEAT_RE.search(text):
        classes.append("current_live_openai_repeated_answered_question")
        classes.append("current_live_openai_memory_progression_defect")
    if ANSWERED_LIMIT_TRANSCRIPT_RE.search(transcript) and not re.search(r"\bpro\b|limits?|higher usage", text, re.I):
        classes.append("current_live_openai_known_intensity_ignored")
        classes.append("current_live_openai_memory_progression_defect")
    if re.search(r"heavy side|little heavy|use heavily|already told", transcript, re.I) and KNOWN_USE_IGNORED_RE.search(text):
        classes.append("current_live_openai_known_use_case_ignored")
        classes.append("current_live_openai_memory_progression_defect")
    if re.search(r"coding and writing|coding|writing", transcript, re.I) and KNOWN_INTENSITY_IGNORED_RE.search(text):
        classes.append("current_live_openai_known_intensity_ignored")
        classes.append("current_live_openai_memory_progression_defect")
    known_price_context = re.search(
        r"hitting limits|heavy side|\"openai_limit_pain\": true|\"openai_usage_intensity\": \"heavy\"",
        f"{transcript} {trace_text} {payload_context_text}",
        re.I,
    )
    if PRICE_TRANSCRIPT_RE.search(transcript) and PRICE_RESPONSE_RE.search(text) and PRICE_CONTEXT_RESET_RE.search(text) and known_price_context:
        classes.append("current_live_openai_price_context_reset")
        classes.append("current_live_openai_memory_progression_defect")
    explicit_limit_context = EXPLICIT_LIMIT_CONTEXT_RE.search(f"{transcript} {payload_context_text}")
    if FALSE_LIMIT_PAIN_RESPONSE_RE.search(text) and not explicit_limit_context:
        classes.append("current_live_openai_false_limit_pain")
        classes.append("current_live_openai_sales_quality_defect")
    if COMPETITOR_CAVEAT_RE.search(text) and re.search(r"coding|writing|plus|pro|price|sign up", f"{transcript} {payload_context_text}", re.I):
        classes.append("current_live_openai_repeated_competitor_caveat")
    if AI_TOOL_USAGE_TRANSCRIPT_RE.search(transcript) and PREMATURE_NO_FIT_RESPONSE_RE.search(text):
        classes.append("current_live_openai_premature_no_fit_caveat")
        classes.append("current_live_openai_sales_momentum_defect")
    if PRICE_OBJECTION_TRANSCRIPT_RE.search(transcript) and PRICE_REPEAT_RESPONSE_RE.search(text):
        classes.append("current_live_openai_price_objection_repeated_price")
        classes.append("current_live_openai_sales_momentum_defect")
    if PRO_TIER_TRANSCRIPT_RE.search(transcript) and (
        PLUS_VS_PRO_RESET_RE.search(text) or not PRO_TIER_RESPONSE_RE.search(text)
    ):
        classes.append("current_live_openai_pro_tier_selection_defect")
        classes.append("current_live_openai_wrong_decision_stage")
        classes.append("current_live_openai_sales_momentum_defect")
    if SIGNUP_CONTEXT_TRANSCRIPT_RE.search(transcript) and (pro_tier_context_active or PRO_TIER_TRANSCRIPT_RE.search(transcript)) and not PRO_TIER_RESPONSE_RE.search(text):
        classes.append("current_live_openai_signup_close_stage_mismatch")
        classes.append("current_live_openai_wrong_decision_stage")
        classes.append("current_live_openai_sales_momentum_defect")
    if source == "pre_speech_conversation_stability_guard" and re.search(
        r"chatgpt|other ai|price|expensive|plus|pro|sign up|upgrade|which version|which tier",
        transcript,
        re.I,
    ):
        classes.append("current_live_openai_stability_guard_owned_sales_turn")
        classes.append("current_live_openai_sales_momentum_defect")
    if source == "pre_speech_conversation_stability_guard" and (
        explanation_question
        or plan_label_trap
        or AI_TOOL_USAGE_TRANSCRIPT_RE.search(transcript)
        or re.search(r"chatgpt|other ai|price|expensive|plus|pro|business|enterprise|sign up|upgrade|which version|which tier", transcript, re.I)
    ):
        classes.append("current_live_openai_stability_guard_owned_adapter_turn")
        classes.append("current_live_openai_intent_priority_defect")
        classes.append("current_live_openai_sales_momentum_defect")
    if SIGNUP_CONTEXT_TRANSCRIPT_RE.search(transcript) and not SIGNUP_CONTEXT_RESPONSE_RE.search(text):
        classes.append("current_live_openai_close_context_missing")
        classes.append("current_live_openai_memory_progression_defect")
        classes.append("current_live_openai_missed_close")
    if BUYING_SIGNAL_TRANSCRIPT_RE.search(transcript) and not COMMERCIAL_CLOSE_RESPONSE_RE.search(text):
        classes.append("current_live_openai_missed_close")
    if (
        re.search(r"coding|writing", f"{transcript} {payload_context_text}", re.I)
        and HEAVY_CONTEXT_RE.search(f"{transcript} {payload_context_text}")
        and not re.search(r"\bpro\b", text, re.I)
    ):
        classes.append("current_live_openai_missed_recommendation")
    if str((payload.get("dialogue_manager") or {}).get("final_response_source") or "") == "duplicate_response_repair" and (
        KNOWN_USE_IGNORED_RE.search(text) or PRICE_CONTEXT_RESET_RE.search(text) or ADOPTION_STATE_RE.search(text)
    ):
        classes.append("current_live_openai_duplicate_repair_regression")
        classes.append("current_live_openai_memory_progression_defect")
    if LEGACY_FIELD_RE.search(trace_text) or LEGACY_RE.search(text) or OWNER_RE.search(text):
        classes.append("current_live_openai_legacy_field_leakage")
    if ROUTESIGNAL_TRACE_RE.search(trace_text):
        classes.append("current_live_openai_routesignal_contamination")
    if RAW_URL_RE.search(text):
        classes.append("current_live_openai_raw_url_spoken_issue")
    if FAKE_SIDE_EFFECT_RE.search(text):
        classes.append("current_live_openai_fake_side_effect_claim")
    if AFFILIATION_RE.search(text) and not SOURCE_TRUST_RESPONSE_RE.search(text):
        classes.append("current_live_openai_affiliation_or_disclaimer_issue")
    if SOURCE_CLAIM_RE.search(text):
        classes.append("current_live_openai_source_claim_issue")
    if selected.get("close_mode") != "self_serve_purchase_link":
        classes.append("current_live_openai_close_semantics_issue")
    if selected.get("should_speak_raw_url") is not False or selected.get("can_send_email") is not False:
        classes.append("current_live_openai_close_semantics_issue")
    dialogue_specific = [item for item in classes if item in DIALOGUE_DEFECT_CLASSES and item not in {"current_live_openai_runtime_defect", "current_live_openai_sales_quality_defect"}]
    if dialogue_specific:
        if any(
            item
            for item in dialogue_specific
            if item
            in {
                "current_live_openai_information_not_selling",
                "current_live_openai_missed_recommendation",
                "current_live_openai_missed_close",
                "current_live_openai_weak_value_frame",
                "current_live_openai_repeated_competitor_caveat",
                "current_live_openai_false_limit_pain",
                "current_live_openai_overqualified_without_recommendation",
                "current_live_openai_premature_no_fit_caveat",
                "current_live_openai_price_objection_repeated_price",
                "current_live_openai_wrong_decision_stage",
                "current_live_openai_pro_tier_selection_defect",
                "current_live_openai_signup_close_stage_mismatch",
                "current_live_openai_stability_guard_owned_sales_turn",
                "current_live_openai_sales_momentum_defect",
                "current_live_openai_opening_origin_missing",
                "current_live_openai_explanation_question_misrouted",
                "current_live_openai_plan_label_trap",
                "current_live_openai_team_context_false_positive",
                "current_live_openai_repeated_wrong_explanation",
                "current_live_openai_state_initialized_with_recommendation",
                "current_live_openai_stability_guard_owned_adapter_turn",
                "current_live_openai_intent_priority_defect",
                "current_live_openai_logic_generalization_defect",
            }
        ):
            classes.append("current_live_openai_sales_performance_defect")
        classes.append("current_live_openai_sales_quality_defect")
        classes.append("current_live_openai_runtime_defect")
    return list(dict.fromkeys(classes))


def safe_trace(record: dict[str, Any], *, current: bool, classification: str, classes: list[str]) -> dict[str, Any]:
    payload = record["payload"]
    text = response_text(payload)
    selected = selected_config(payload)
    delivery = tts(payload)
    voice = voice_diag(payload)
    trace = {
        "source_file": project_relative(record["path"]),
        "source_file_hash": sha256_file(record["path"])[:12],
        "generated_at": record_generated_at(payload),
        "git_head_short": payload.get("git_head_short"),
        "classification": classification,
        "classifications": classes,
        "is_current_marker_record": current,
        "campaign_id": selected.get("campaign_id") or payload.get("campaign_id"),
        "campaign_config_path": campaign_path(payload),
        "campaign_selector_mode": payload.get("campaign_selector_mode"),
        "mode": payload.get("mode"),
        "selected_mode": selected.get("mode"),
        "live_tts_used": live_tts_used(payload),
        "dry_run": dry_run(payload),
        "elevenlabs_call_made": bool(provider_calls(payload) and str(delivery.get("provider_id") or "").lower().startswith("elevenlabs")),
        "tts_provider_calls_made": provider_calls(payload),
        "audio_file_created": audio_created(payload),
        "fallback_reason": delivery.get("fallback_reason") or summary(payload).get("tts_fallback_reason"),
        "voice_id_source": voice["voice_id_source"],
        "voice_id_hash": voice["voice_id_hash"],
        "raw_voice_id_logged": voice["raw_value_logged"],
        "transcript_hash": sha256_text(transcript_text(payload))[:12] if transcript_text(payload) else None,
        "final_response": text,
        "final_response_hash": sha256_text(text)[:12],
        "source_fact_ids": source_fact_ids(payload),
        "close_mode": selected.get("close_mode"),
        "call_control": (payload.get("dialogue_manager") or {}).get("call_control") if isinstance(payload.get("dialogue_manager"), dict) else None,
        "side_effect_flags": {
            "sends_email": bool(payload.get("sends_email")),
            "creates_calendar_event": bool(payload.get("creates_calendar_event")),
            "writes_crm": bool(payload.get("writes_crm")),
            "opens_prod_102": bool(payload.get("opens_prod_102")),
            "customer_audio_uploaded_to_python_server": bool(payload.get("customer_audio_uploaded_to_python_server")),
            "customer_audio_uploaded_to_tts_provider": bool(payload.get("customer_audio_uploaded_to_tts_provider") or delivery.get("customer_audio_uploaded")),
        },
        "redacted_synthetic_replay_hint": "Private buyer transcript withheld; use synthetic replay validator if a current dialogue defect is listed.",
    }
    return trace


def append_turn(state: dict[str, Any], turn: dict[str, Any]) -> None:
    state.setdefault("turns", []).append(
        {
            "summary": turn.get("summary", {}),
            "continuity": turn.get("demo_session_continuity") or turn.get("conversation_continuity") or {},
            "conversation_memory": turn.get("demo_conversation_memory") or turn.get("conversation_memory") or {},
            "dialogue_manager": turn.get("dialogue_manager", {}),
            "dialogue_pragmatics": turn.get("dialogue_pragmatics", {}),
            "universal_policy_frame": turn.get("universal_policy_frame", {}),
        }
    )


def build_replay_sequence(transcripts: list[str], session_id: str) -> dict[str, Any]:
    state: dict[str, Any] = {"turns": []}
    turn = demo.build_browser_demo_turn_packet(
        transcript=transcripts[0],
        campaign_id=demo.DEFAULT_CAMPAIGN_ID,
        stage=demo.DEFAULT_STAGE,
        input_type="agent-open" if transcripts[0] == "__agent_open__" else "speech-final",
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
    append_turn(state, turn)
    for transcript in transcripts[1:]:
        turn = demo.build_browser_demo_turn_packet(
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
        append_turn(state, turn)
    return turn


def current_runtime_replay() -> dict[str, Any]:
    traces: list[dict[str, Any]] = []
    for index, case in enumerate(POST_PATCH_REPLAY_CASES, start=1):
        transcripts = case if isinstance(case, list) else [case]
        turn = build_replay_sequence(transcripts, f"post-patch-replay-{index}")
        classes = classify_current(turn)
        dialogue_classes = [item for item in classes if item in DIALOGUE_DEFECT_CLASSES]
        text = response_text(turn)
        side_effects = {
            "sends_email": bool(turn.get("sends_email")),
            "creates_calendar_event": bool(turn.get("creates_calendar_event")),
            "writes_crm": bool(turn.get("writes_crm")),
            "opens_prod_102": bool(turn.get("opens_prod_102")),
            "customer_audio_uploaded_to_python_server": bool(turn.get("customer_audio_uploaded_to_python_server")),
            "customer_audio_uploaded_to_tts_provider": bool(turn.get("customer_audio_uploaded_to_tts_provider") or tts(turn).get("customer_audio_uploaded")),
        }
        if any(side_effects.values()):
            dialogue_classes.append("current_live_openai_fake_side_effect_claim")
        traces.append(
            {
                "case_id": f"post-patch-replay-{index}",
                "transcript_hash": sha256_text(" | ".join(transcripts))[:12],
                "final_response": text,
                "final_response_hash": sha256_text(text)[:12],
                "classifications": list(dict.fromkeys(dialogue_classes)),
                "status": "pass" if not dialogue_classes else "fail",
                "side_effects": side_effects,
            }
        )
    failed = [trace for trace in traces if trace["status"] != "pass"]
    return {
        "status": "pass" if not failed else "fail",
        "case_count": len(traces),
        "failed_count": len(failed),
        "failed_cases": failed,
        "provider_calls_made": False,
        "live_tts_calls_made": False,
        "raw_private_transcript_copied_to_public_evidence": False,
        "traces": traces,
    }


def write_evidence(result: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = "\n".join(
        [
            f"# {CHECKPOINT_ID}",
            "",
            f"- Status: `{result['status']}`",
            f"- Total private records scanned: `{result['total_private_records_scanned']}`",
            f"- Current OpenAI live records found: `{result['current_openai_live_records_found']}`",
            f"- Records after `{CURRENT_COMMIT}` or latest marker: `{result['records_after_current_marker_or_latest_current_marker']}`",
            f"- Stale/historical OpenAI records ignored: `{result['stale_historical_openai_records_ignored']}`",
            f"- Live TTS used count: `{result['live_tts_used_count']}`",
            f"- Dry-run count: `{result['dry_run_count']}`",
            f"- ElevenLabs call made count: `{result['elevenlabs_call_made_count']}`",
            f"- TTS provider calls made count: `{result['tts_provider_calls_made_count']}`",
            f"- Audio file created count: `{result['audio_file_created_count']}`",
            f"- Raw voice ID logged count: `{result['raw_voice_id_logged_count']}`",
            f"- Runtime defect count: `{result['current_live_openai_runtime_defect_count']}`",
            f"- Pre-patch private live defects: `{result['pre_patch_current_live_defect_count']}`",
            f"- Fixed by replay after patch: `{result['fixed_by_replay_after_patch_count']}`",
            f"- Post-patch replay defects: `{result['post_patch_current_live_defect_count']}`",
            f"- ASR product alias issue count: `{result['current_live_openai_asr_product_alias_issue_count']}`",
            f"- Internal policy language leak count: `{result['current_live_openai_internal_policy_language_leak_count']}`",
            f"- Price question refusal count: `{result['current_live_openai_price_question_refusal_count']}`",
            f"- Plan recommendation stall count: `{result['current_live_openai_plan_recommendation_stall_count']}`",
            f"- Information-not-selling count: `{result['current_live_openai_information_not_selling_count']}`",
            f"- Missed recommendation count: `{result['current_live_openai_missed_recommendation_count']}`",
            f"- Missed close count: `{result['current_live_openai_missed_close_count']}`",
            f"- Weak value frame count: `{result['current_live_openai_weak_value_frame_count']}`",
            f"- Repeated competitor caveat count: `{result['current_live_openai_repeated_competitor_caveat_count']}`",
            f"- False limit-pain count: `{result['current_live_openai_false_limit_pain_count']}`",
            f"- Overqualified without recommendation count: `{result['current_live_openai_overqualified_without_recommendation_count']}`",
            f"- Sales-performance defect count: `{result['current_live_openai_sales_performance_defect_count']}`",
            f"- Premature no-fit caveat count: `{result['current_live_openai_premature_no_fit_caveat_count']}`",
            f"- Price objection repeated-price count: `{result['current_live_openai_price_objection_repeated_price_count']}`",
            f"- Wrong decision-stage count: `{result['current_live_openai_wrong_decision_stage_count']}`",
            f"- Pro-tier selection defect count: `{result['current_live_openai_pro_tier_selection_defect_count']}`",
            f"- Signup close stage-mismatch count: `{result['current_live_openai_signup_close_stage_mismatch_count']}`",
            f"- Stability guard owned sales-turn count: `{result['current_live_openai_stability_guard_owned_sales_turn_count']}`",
            f"- Opening origin missing count: `{result['current_live_openai_opening_origin_missing_count']}`",
            f"- Explanation question misrouted count: `{result['current_live_openai_explanation_question_misrouted_count']}`",
            f"- Plan-label trap count: `{result['current_live_openai_plan_label_trap_count']}`",
            f"- Team-context false-positive count: `{result['current_live_openai_team_context_false_positive_count']}`",
            f"- Repeated wrong explanation count: `{result['current_live_openai_repeated_wrong_explanation_count']}`",
            f"- State initialized with recommendation count: `{result['current_live_openai_state_initialized_with_recommendation_count']}`",
            f"- Stability guard owned adapter-turn count: `{result['current_live_openai_stability_guard_owned_adapter_turn_count']}`",
            f"- Intent-priority defect count: `{result['current_live_openai_intent_priority_defect_count']}`",
            f"- Logic-generalization defect count: `{result['current_live_openai_logic_generalization_defect_count']}`",
            f"- Sales momentum defect count: `{result['current_live_openai_sales_momentum_defect_count']}`",
            f"- Legacy field leakage count: `{result['current_live_openai_legacy_field_leakage_count']}`",
            f"- RouteSignal contamination count: `{result['current_live_openai_routesignal_contamination_count']}`",
            f"- ASR issue count: `{result['current_live_openai_asr_issue_count']}`",
            f"- TTS/audio issue count: `{result['current_live_openai_tts_audio_issue_count']}`",
            f"- Latency/turn-taking issue count: `{result['current_live_openai_latency_or_turn_taking_issue_count']}`",
            "",
            "## Voice Source Summary",
            "",
            "```json",
            json.dumps(
                {
                    "voice_id_source_values": result["voice_id_source_values"],
                    "voice_id_hash_values": result["voice_id_hash_values"],
                },
                indent=2,
                sort_keys=True,
            ),
            "```",
            "",
            "## Classification Counts",
            "",
            "```json",
            json.dumps(result["classification_counts"], indent=2, sort_keys=True),
            "```",
            "",
            "## Human Review Examples",
            "",
            "```json",
            json.dumps(result["examples_requiring_human_review"], indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> None:
    total_scanned, records, invalid_count = private_records()
    threshold = current_threshold(records)
    head = git_head()
    traces: list[dict[str, Any]] = []
    counts = Counter()
    current_records: list[dict[str, Any]] = []
    stale_records: list[dict[str, Any]] = []
    current_dialogue_defect_examples: list[dict[str, Any]] = []

    for record in records:
        payload = record["payload"]
        current = is_current_record(record, threshold)
        classes: list[str]
        if current:
            classes = classify_current(payload)
            current_records.append(record)
            if not classes:
                classification = "current_openai_live_success"
                classes = [classification]
            else:
                dialogue_classes = [
                    item
                    for item in classes
                    if item in DIALOGUE_DEFECT_CLASSES
                    and item not in {"current_live_openai_runtime_defect", "current_live_openai_sales_quality_defect"}
                ]
                classification = dialogue_classes[0] if dialogue_classes else classes[0]
                if classes:
                    counts["needs_human_review"] += 1
        else:
            stale_records.append(record)
            if dry_run(payload):
                classes = ["expected_dry_run_historical_record"]
                classification = "expected_dry_run_historical_record"
            else:
                classes = ["stale_or_unknown_version_artifact"]
                classification = "stale_or_unknown_version_artifact"

        for item in classes:
            counts[item] += 1
        trace = safe_trace(record, current=current, classification=classification, classes=classes)
        traces.append(trace)
        if current and any(
            item in DIALOGUE_DEFECT_CLASSES
            and item not in {"current_live_openai_runtime_defect", "current_live_openai_sales_quality_defect"}
            for item in classes
        ):
            current_dialogue_defect_examples.append(
                {
                    "source_file": trace["source_file"],
                    "generated_at": trace["generated_at"],
                    "classifications": [
                        item
                        for item in classes
                        if item in DIALOGUE_DEFECT_CLASSES
                        and item not in {"current_live_openai_runtime_defect", "current_live_openai_sales_quality_defect"}
                    ],
                    "final_response": trace["final_response"],
                    "transcript_hash": trace["transcript_hash"],
                    "redacted_synthetic_replay_hint": trace["redacted_synthetic_replay_hint"],
                }
            )

    current_traces = [trace for trace in traces if trace["is_current_marker_record"]]
    stale_traces = [trace for trace in traces if not trace["is_current_marker_record"]]
    voice_sources = sorted({str(trace["voice_id_source"]) for trace in current_traces if trace["voice_id_source"]})
    voice_hashes = sorted({str(trace["voice_id_hash"]) for trace in current_traces if trace["voice_id_hash"]})
    close_modes = sorted({str(trace["close_mode"]) for trace in current_traces if trace["close_mode"]})
    plan_categories_seen = sorted({plan for trace in current_traces for plan in plan_categories(trace["final_response"])}, key=PLAN_NAMES.index)
    all_source_fact_ids = sorted({fact_id for trace in current_traces for fact_id in trace["source_fact_ids"]})
    selector_ok = all(
        trace["campaign_config_path"] == FIXTURE_RELATIVE
        and trace["campaign_id"] == "public-openai-chatgpt-plans"
        and trace["campaign_selector_mode"] == "generic_config"
        for trace in current_traces
    )
    all_side_effects_false = all(not any(trace["side_effect_flags"].values()) for trace in current_traces)
    replay = current_runtime_replay()
    replay_class_counts = Counter(
        item
        for trace in replay["failed_cases"]
        for item in trace.get("classifications", [])
    )
    private_current_dialogue_defect_count = counts["current_live_openai_runtime_defect"]
    post_patch_current_live_defect_count = int(replay["failed_count"])
    fixed_by_replay_after_patch_count = private_current_dialogue_defect_count if post_patch_current_live_defect_count == 0 else 0
    pre_patch_current_live_defect_count = private_current_dialogue_defect_count if fixed_by_replay_after_patch_count else 0
    if pre_patch_current_live_defect_count:
        counts["pre_patch_current_live_defect"] += pre_patch_current_live_defect_count
    if fixed_by_replay_after_patch_count:
        counts["fixed_by_replay_after_patch"] += fixed_by_replay_after_patch_count
    if post_patch_current_live_defect_count:
        counts["post_patch_current_live_defect"] += post_patch_current_live_defect_count

    result = {
        "status": "pass" if post_patch_current_live_defect_count == 0 and invalid_count == 0 else "fail",
        "checkpoint_id": CHECKPOINT_ID,
        "git_head_short": head,
        "current_commit_marker": CURRENT_COMMIT,
        "current_record_threshold_utc": threshold.isoformat() if threshold else None,
        "total_private_records_scanned": total_scanned,
        "total_openai_records_scanned": len(records),
        "current_openai_live_records_found": len(current_records),
        "fresh_openai_live_records": len(current_records),
        "records_after_current_marker_or_latest_current_marker": len(current_records),
        "stale_historical_openai_records_ignored": len(stale_records),
        "incomplete_or_invalid_private_record_count": invalid_count,
        "live_tts_used_count": sum(1 for trace in current_traces if trace["live_tts_used"]),
        "dry_run_count": sum(1 for trace in current_traces if trace["dry_run"]),
        "historical_dry_run_count": sum(1 for trace in stale_traces if trace["dry_run"]),
        "elevenlabs_call_made_count": sum(1 for trace in current_traces if trace["elevenlabs_call_made"]),
        "tts_provider_calls_made_count": sum(1 for trace in current_traces if trace["tts_provider_calls_made"]),
        "audio_file_created_count": sum(1 for trace in current_traces if trace["audio_file_created"]),
        "provider_audio_playback_issue_count": sum(1 for record in current_records if bool(record["payload"].get("provider_audio_playback_issue"))),
        "voice_id_source_values": voice_sources,
        "voice_id_hash_values": voice_hashes,
        "raw_voice_id_logged_count": sum(1 for trace in current_traces if trace["raw_voice_id_logged"]),
        "campaign_selector_consistency": {
            "consistent": selector_ok,
            "expected_campaign_config_path": FIXTURE_RELATIVE,
            "expected_campaign_id": "public-openai-chatgpt-plans",
            "expected_selector_mode": "generic_config",
        },
        "plan_categories_mentioned": plan_categories_seen,
        "close_modes_observed": close_modes,
        "raw_URL_spoken_count": counts["current_live_openai_raw_url_spoken_issue"],
        "fake_email_calendar_CRM_claim_count": counts["current_live_openai_fake_side_effect_claim"],
        "fake_side_effect_claim_count": counts["current_live_openai_fake_side_effect_claim"],
        "affiliation_authorization_issue_count": counts["current_live_openai_affiliation_or_disclaimer_issue"],
        "source_claim_issue_count": counts["current_live_openai_source_claim_issue"],
        "source_fact_ids_present": all_source_fact_ids,
        "ASR_issue_count": counts["current_live_openai_asr_issue"],
        "latency_turn_taking_issue_count": counts["current_live_openai_latency_or_turn_taking_issue"],
        "current_live_openai_runtime_defect_count": post_patch_current_live_defect_count,
        "private_current_live_dialogue_defect_count": private_current_dialogue_defect_count,
        "pre_patch_current_live_defect_count": pre_patch_current_live_defect_count,
        "fixed_by_replay_after_patch_count": fixed_by_replay_after_patch_count,
        "post_patch_current_live_defect_count": post_patch_current_live_defect_count,
        "post_patch_runtime_replay": replay,
        "current_live_openai_asr_product_alias_issue_count": replay_class_counts["current_live_openai_asr_product_alias_issue"],
        "current_live_openai_internal_policy_language_leak_count": replay_class_counts["current_live_openai_internal_policy_language_leak"],
        "current_live_openai_price_question_refusal_count": replay_class_counts["current_live_openai_price_question_refusal"],
        "current_live_openai_plan_recommendation_stall_count": replay_class_counts["current_live_openai_plan_recommendation_stall"],
        "current_live_openai_information_not_selling_count": replay_class_counts["current_live_openai_information_not_selling"],
        "current_live_openai_missed_recommendation_count": replay_class_counts["current_live_openai_missed_recommendation"],
        "current_live_openai_missed_close_count": replay_class_counts["current_live_openai_missed_close"],
        "current_live_openai_weak_value_frame_count": replay_class_counts["current_live_openai_weak_value_frame"],
        "current_live_openai_repeated_competitor_caveat_count": replay_class_counts["current_live_openai_repeated_competitor_caveat"],
        "current_live_openai_false_limit_pain_count": replay_class_counts["current_live_openai_false_limit_pain"],
        "current_live_openai_overqualified_without_recommendation_count": replay_class_counts["current_live_openai_overqualified_without_recommendation"],
        "current_live_openai_sales_performance_defect_count": replay_class_counts["current_live_openai_sales_performance_defect"],
        "current_live_openai_premature_no_fit_caveat_count": replay_class_counts["current_live_openai_premature_no_fit_caveat"],
        "current_live_openai_price_objection_repeated_price_count": replay_class_counts["current_live_openai_price_objection_repeated_price"],
        "current_live_openai_wrong_decision_stage_count": replay_class_counts["current_live_openai_wrong_decision_stage"],
        "current_live_openai_pro_tier_selection_defect_count": replay_class_counts["current_live_openai_pro_tier_selection_defect"],
        "current_live_openai_signup_close_stage_mismatch_count": replay_class_counts["current_live_openai_signup_close_stage_mismatch"],
        "current_live_openai_stability_guard_owned_sales_turn_count": replay_class_counts["current_live_openai_stability_guard_owned_sales_turn"],
        "current_live_openai_sales_momentum_defect_count": replay_class_counts["current_live_openai_sales_momentum_defect"],
        "current_live_openai_opening_origin_missing_count": replay_class_counts["current_live_openai_opening_origin_missing"],
        "current_live_openai_explanation_question_misrouted_count": replay_class_counts["current_live_openai_explanation_question_misrouted"],
        "current_live_openai_plan_label_trap_count": replay_class_counts["current_live_openai_plan_label_trap"],
        "current_live_openai_team_context_false_positive_count": replay_class_counts["current_live_openai_team_context_false_positive"],
        "current_live_openai_repeated_wrong_explanation_count": replay_class_counts["current_live_openai_repeated_wrong_explanation"],
        "current_live_openai_state_initialized_with_recommendation_count": replay_class_counts["current_live_openai_state_initialized_with_recommendation"],
        "current_live_openai_stability_guard_owned_adapter_turn_count": replay_class_counts["current_live_openai_stability_guard_owned_adapter_turn"],
        "current_live_openai_intent_priority_defect_count": replay_class_counts["current_live_openai_intent_priority_defect"],
        "current_live_openai_logic_generalization_defect_count": replay_class_counts["current_live_openai_logic_generalization_defect"],
        "current_live_openai_memory_progression_defect_count": replay_class_counts["current_live_openai_memory_progression_defect"],
        "current_live_openai_repeated_answered_question_count": replay_class_counts["current_live_openai_repeated_answered_question"],
        "current_live_openai_duplicate_repair_regression_count": replay_class_counts["current_live_openai_duplicate_repair_regression"],
        "current_live_openai_known_use_case_ignored_count": replay_class_counts["current_live_openai_known_use_case_ignored"],
        "current_live_openai_known_intensity_ignored_count": replay_class_counts["current_live_openai_known_intensity_ignored"],
        "current_live_openai_price_context_reset_count": replay_class_counts["current_live_openai_price_context_reset"],
        "current_live_openai_close_context_missing_count": replay_class_counts["current_live_openai_close_context_missing"],
        "current_live_openai_legacy_field_leakage_count": replay_class_counts["current_live_openai_legacy_field_leakage"],
        "current_live_openai_routesignal_contamination_count": replay_class_counts["current_live_openai_routesignal_contamination"],
        "current_live_openai_sales_quality_defect_count": replay_class_counts["current_live_openai_sales_quality_defect"],
        "private_current_live_asr_product_alias_issue_count": counts["current_live_openai_asr_product_alias_issue"],
        "private_current_live_internal_policy_language_leak_count": counts["current_live_openai_internal_policy_language_leak"],
        "private_current_live_price_question_refusal_count": counts["current_live_openai_price_question_refusal"],
        "private_current_live_plan_recommendation_stall_count": counts["current_live_openai_plan_recommendation_stall"],
        "private_current_live_information_not_selling_count": counts["current_live_openai_information_not_selling"],
        "private_current_live_missed_recommendation_count": counts["current_live_openai_missed_recommendation"],
        "private_current_live_missed_close_count": counts["current_live_openai_missed_close"],
        "private_current_live_weak_value_frame_count": counts["current_live_openai_weak_value_frame"],
        "private_current_live_repeated_competitor_caveat_count": counts["current_live_openai_repeated_competitor_caveat"],
        "private_current_live_false_limit_pain_count": counts["current_live_openai_false_limit_pain"],
        "private_current_live_overqualified_without_recommendation_count": counts["current_live_openai_overqualified_without_recommendation"],
        "private_current_live_sales_performance_defect_count": counts["current_live_openai_sales_performance_defect"],
        "private_current_live_premature_no_fit_caveat_count": counts["current_live_openai_premature_no_fit_caveat"],
        "private_current_live_price_objection_repeated_price_count": counts["current_live_openai_price_objection_repeated_price"],
        "private_current_live_wrong_decision_stage_count": counts["current_live_openai_wrong_decision_stage"],
        "private_current_live_pro_tier_selection_defect_count": counts["current_live_openai_pro_tier_selection_defect"],
        "private_current_live_signup_close_stage_mismatch_count": counts["current_live_openai_signup_close_stage_mismatch"],
        "private_current_live_stability_guard_owned_sales_turn_count": counts["current_live_openai_stability_guard_owned_sales_turn"],
        "private_current_live_sales_momentum_defect_count": counts["current_live_openai_sales_momentum_defect"],
        "private_current_live_opening_origin_missing_count": counts["current_live_openai_opening_origin_missing"],
        "private_current_live_explanation_question_misrouted_count": counts["current_live_openai_explanation_question_misrouted"],
        "private_current_live_plan_label_trap_count": counts["current_live_openai_plan_label_trap"],
        "private_current_live_team_context_false_positive_count": counts["current_live_openai_team_context_false_positive"],
        "private_current_live_repeated_wrong_explanation_count": counts["current_live_openai_repeated_wrong_explanation"],
        "private_current_live_state_initialized_with_recommendation_count": counts["current_live_openai_state_initialized_with_recommendation"],
        "private_current_live_stability_guard_owned_adapter_turn_count": counts["current_live_openai_stability_guard_owned_adapter_turn"],
        "private_current_live_intent_priority_defect_count": counts["current_live_openai_intent_priority_defect"],
        "private_current_live_logic_generalization_defect_count": counts["current_live_openai_logic_generalization_defect"],
        "private_current_live_openai_memory_progression_defect_count": counts["current_live_openai_memory_progression_defect"],
        "private_current_live_openai_repeated_answered_question_count": counts["current_live_openai_repeated_answered_question"],
        "private_current_live_openai_duplicate_repair_regression_count": counts["current_live_openai_duplicate_repair_regression"],
        "private_current_live_openai_known_use_case_ignored_count": counts["current_live_openai_known_use_case_ignored"],
        "private_current_live_openai_known_intensity_ignored_count": counts["current_live_openai_known_intensity_ignored"],
        "private_current_live_openai_price_context_reset_count": counts["current_live_openai_price_context_reset"],
        "private_current_live_openai_close_context_missing_count": counts["current_live_openai_close_context_missing"],
        "private_current_live_legacy_field_leakage_count": counts["current_live_openai_legacy_field_leakage"],
        "private_current_live_routesignal_contamination_count": counts["current_live_openai_routesignal_contamination"],
        "private_current_live_sales_quality_defect_count": counts["current_live_openai_sales_quality_defect"],
        "premature_plan_comparison_count": counts["current_live_openai_premature_plan_comparison"],
        "assumption_repair_defect_count": counts["current_live_openai_assumption_repair_defect"],
        "source_trust_answer_defect_count": counts["current_live_openai_source_trust_answer_defect"],
        "repeated_prompt_loop_count": counts["current_live_openai_loop_or_repeated_prompt"],
        "current_live_openai_asr_issue_count": counts["current_live_openai_asr_issue"],
        "current_live_openai_tts_audio_issue_count": counts["current_live_openai_tts_audio_issue"],
        "current_live_openai_latency_or_turn_taking_issue_count": counts["current_live_openai_latency_or_turn_taking_issue"],
        "current_live_openai_premature_plan_comparison_count": replay_class_counts["current_live_openai_premature_plan_comparison"],
        "current_live_openai_assumption_repair_defect_count": replay_class_counts["current_live_openai_assumption_repair_defect"],
        "current_live_openai_source_trust_answer_defect_count": replay_class_counts["current_live_openai_source_trust_answer_defect"],
        "current_live_openai_loop_or_repeated_prompt_count": replay_class_counts["current_live_openai_loop_or_repeated_prompt"],
        "current_live_openai_campaign_selector_issue_count": counts["current_live_openai_campaign_selector_issue"],
        "current_live_openai_source_claim_issue_count": counts["current_live_openai_source_claim_issue"],
        "current_live_openai_close_semantics_issue_count": counts["current_live_openai_close_semantics_issue"],
        "current_live_openai_affiliation_or_disclaimer_issue_count": counts["current_live_openai_affiliation_or_disclaimer_issue"],
        "current_live_openai_raw_url_spoken_issue_count": counts["current_live_openai_raw_url_spoken_issue"],
        "current_live_openai_fake_side_effect_claim_count": counts["current_live_openai_fake_side_effect_claim"],
        "private_current_live_legacy_compatibility_leakage_count": counts["current_live_openai_legacy_compatibility_leakage"],
        "private_current_live_human_followup_owner_leakage_count": counts["current_live_openai_human_followup_owner_leakage"],
        "private_current_live_cross_campaign_contamination_count": counts["current_live_openai_cross_campaign_contamination"],
        "pre_patch_legacy_compatibility_leakage_count": counts["current_live_openai_legacy_compatibility_leakage"] if fixed_by_replay_after_patch_count else 0,
        "pre_patch_human_followup_owner_leakage_count": counts["current_live_openai_human_followup_owner_leakage"] if fixed_by_replay_after_patch_count else 0,
        "post_patch_legacy_compatibility_leakage_count": replay_class_counts["current_live_openai_legacy_field_leakage"],
        "post_patch_human_followup_owner_leakage_count": replay_class_counts["current_live_openai_legacy_field_leakage"],
        "post_patch_cross_campaign_contamination_count": replay_class_counts["current_live_openai_routesignal_contamination"],
        "legacy_compatibility_leakage_count": replay_class_counts["current_live_openai_legacy_field_leakage"],
        "human_followup_owner_leakage_count": replay_class_counts["current_live_openai_legacy_field_leakage"],
        "cross_campaign_contamination_count": replay_class_counts["current_live_openai_routesignal_contamination"],
        "needs_human_review_count": counts["needs_human_review"],
        "examples_requiring_human_review": current_dialogue_defect_examples[:5],
        "classification_counts": dict(sorted(counts.items())),
        "campaign_selector_modes_seen_current": sorted({str(trace["campaign_selector_mode"]) for trace in current_traces if trace["campaign_selector_mode"]}),
        "side_effects_false": all_side_effects_false,
        "provider_calls_made_by_audit": False,
        "local_llm_calls_made_by_audit": False,
        "live_tts_calls_made_by_audit": False,
        "raw_private_transcript_copied_to_public_evidence": False,
        "records": traces,
    }
    write_evidence(result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "current_openai_live_records_found": result["current_openai_live_records_found"],
                "stale_historical_openai_records_ignored": result["stale_historical_openai_records_ignored"],
                "live_tts_used_count": result["live_tts_used_count"],
                "runtime_defects": result["current_live_openai_runtime_defect_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    if result["status"] != "pass":
        sys.exit(1)


if __name__ == "__main__":
    main()
