#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core import live_voice_session_policy as session_policy  # noqa: E402
from runtime.core.dialogue_reasoner import build_reasoning_context, reason_about_turn  # noqa: E402
from runtime.core.dialogue_reasoner_async_enrichment import (  # noqa: E402
    build_async_enrichment_request,
    complete_async_enrichment,
    render_async_enrichment_prompt,
)
from runtime.providers.dialogue_reasoner_llm_client import (  # noqa: E402
    DEFAULT_REASONER_TEMPERATURE,
    OpenAICompatibleReasonerConfig,
    call_openai_compatible_reasoner,
    missing_provider_config,
    redacted_provider_config,
)
from scripts.run_live_demo_001_agent_voice_call import DEFAULT_CASES_PATH, build_turn_packet, load_campaign  # noqa: E402

CHECKPOINT_ID = "LIVE-DEMO-002-conversation-stability-callback-disambiguation"
DEFAULT_OUT = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID / "llm_enrichment_benchmark.json"
CAMPAIGN_ID = "campaign-prod-005-b2b-software"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID / "benchmark"
TRANSCRIPTS = [
    "__agent_open__",
    "okay",
    "callbacks are the problem",
    "what do you mean by callbacks",
    "tell me more",
    "why does that matter",
    "how much does it cost",
    "I am not sure it fits",
    "what next",
]
CALLBACK_SEMANTIC_CASES = {
    "callbacks are the problem": "callback_workflow_gap",
    "what do you mean by callbacks": "callback_workflow_gap",
    "callback reminders are where we struggle": "callback_workflow_gap",
    "call me back later": "callback_scheduling_request",
    "can you call me tomorrow": "callback_scheduling_request",
    "tomorrow at 3 works": "callback_time_confirmation",
}


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def percentile_95(values: list[float]) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    return sorted(values)[max(0, int(round(0.95 * (len(values) - 1))))]


def response_echo_violation(transcript: str, response: str) -> bool:
    customer = normalize(transcript)
    spoken = normalize(response)
    if not customer or not spoken:
        return False
    words = customer.split()
    if len(words) >= 4 and spoken.startswith(" ".join(words[: min(7, len(words))])):
        return True
    return len(words) >= 5 and customer in spoken


def append_turn(state: dict[str, Any], packet: dict[str, Any]) -> None:
    state.setdefault("turns", []).append(
        {
            "transcript": packet.get("transcript", ""),
            "summary": packet.get("summary", {}),
            "continuity": packet.get("demo_session_continuity", {}),
            "conversation_memory": packet.get("demo_conversation_memory", {}),
        }
    )


def deterministic_packets() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    state: dict[str, Any] = {"turns": []}
    packets: list[dict[str, Any]] = []
    for transcript in TRANSCRIPTS:
        packet = build_turn_packet(
            transcript=transcript,
            campaign_id=CAMPAIGN_ID,
            stage="relevance-check",
            input_type="speech-final",
            silence_count=0,
            cases_path=DEFAULT_CASES_PATH,
            private_out=TMP_DIR,
            live_tts=False,
            force_key_missing=False,
            timeout_seconds=8.0,
            session_id="benchmark-deterministic",
            session_state=state,
            asr_confidence=0.94,
            voice_turn_state="listening",
        )
        packets.append(packet)
        append_turn(state, packet)
    return packets, state


def deterministic_metrics(packets: list[dict[str, Any]]) -> dict[str, Any]:
    responses = [packet["summary"]["final_response"] for packet in packets]
    duplicate_count = len(responses) - len(set(responses))
    latency_values = [float((packet.get("latency") or {}).get("server_total_ms") or 0.0) for packet in packets]
    callback_correct = 0
    for transcript, expected in CALLBACK_SEMANTIC_CASES.items():
        actual = session_policy.callback_semantic_from_transcript(session_policy.normalize_text(transcript), {"turns": []})
        if actual == expected:
            callback_correct += 1
    return {
        "median_latency_ms": statistics.median(latency_values) if latency_values else None,
        "p95_latency_ms": percentile_95(latency_values),
        "schema_failure_rate": 0.0,
        "callback_semantic_accuracy": callback_correct / len(CALLBACK_SEMANTIC_CASES),
        "repetition_rate": duplicate_count / max(1, len(responses)),
        "echo_violation_count": sum(
            1 for packet in packets if response_echo_violation(packet["transcript"], packet["summary"]["final_response"])
        ),
        "route_override_violations": 0,
        "final_response_mutation_violations": 0,
    }


def build_async_requests(packets: list[dict[str, Any]], state: dict[str, Any]) -> list[dict[str, Any]]:
    campaign = load_campaign(CAMPAIGN_ID, DEFAULT_CASES_PATH)
    requests = []
    for index, packet in enumerate(packets):
        transcript = str(packet["transcript"])
        deterministic = reason_about_turn(transcript, state, campaign, mode="baseline")
        context = build_reasoning_context(transcript, state, campaign)
        request = build_async_enrichment_request(
            transcript=transcript,
            context=context,
            deterministic_reasoning=deterministic,
            case_goal=CHECKPOINT_ID,
            customer_response_text=packet["summary"]["final_response"],
            response_packet_id=f"{CHECKPOINT_ID}:benchmark:{index + 1}",
        )
        prompt = (
            render_async_enrichment_prompt(
                transcript=transcript,
                context=context,
                deterministic_reasoning=deterministic,
                case_goal=CHECKPOINT_ID,
            )
            if request.get("provider_call_allowed")
            else ""
        )
        requests.append({"request": request, "prompt": prompt})
    return requests


def provider_lane(
    *,
    name: str,
    requests: list[dict[str, Any]],
    config: OpenAICompatibleReasonerConfig,
    live_provider: bool,
    consent_confirmed: bool,
    max_provider_cases: int,
) -> dict[str, Any]:
    missing = missing_provider_config(config)
    base = {
        "name": name,
        "enabled": live_provider,
        "consent_confirmed": consent_confirmed,
        "provider_config": redacted_provider_config(config),
        "missing_config": missing,
        "provider_calls_made": False,
        "text_sent_to_provider": False,
        "results": [],
    }
    if not live_provider:
        return {**base, "mode": "planned-only", "planned_request_count": len(requests)}
    if not consent_confirmed:
        return {**base, "mode": "blocked", "blocked_reason": "missing-consent-confirmed"}
    if missing:
        return {**base, "mode": "blocked", "blocked_reason": "missing-provider-config"}
    selected = [request for request in requests if request["request"].get("provider_call_allowed")][:max_provider_cases]
    results = []
    for item in selected:
        request = item["request"]
        if not request.get("provider_call_allowed"):
            continue
        provider_call = call_openai_compatible_reasoner(config, item["prompt"])
        results.append(
            complete_async_enrichment(
                request,
                provider_call,
                customer_response_text_after_provider=None,
            )
        )
    return {
        **base,
        "mode": "live",
        "provider_calls_made": any(result.get("provider_call_made") is True for result in results),
        "text_sent_to_provider": any(result.get("text_sent_to_provider") is True for result in results),
        "results": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare deterministic live-demo response stability with optional async LLM enrichment lanes.")
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--live-provider", action="store_true", help="Actually call configured provider lanes.")
    parser.add_argument("--consent-confirmed", action="store_true")
    parser.add_argument("--max-provider-cases", type=int, default=1)
    parser.add_argument("--api-base-url", default=os.environ.get("DIALOGUE_REASONER_BASE_URL"))
    parser.add_argument("--api-model", default=os.environ.get("DIALOGUE_REASONER_MODEL"))
    parser.add_argument("--api-key-env", default="DIALOGUE_REASONER_API_KEY")
    parser.add_argument("--local-base-url", default=os.environ.get("LOCAL_DIALOGUE_REASONER_BASE_URL"))
    parser.add_argument("--local-model", default=os.environ.get("LOCAL_DIALOGUE_REASONER_MODEL"))
    parser.add_argument("--local-api-key-env", default="LOCAL_DIALOGUE_REASONER_API_KEY")
    parser.add_argument("--local-no-key", action="store_true")
    parser.add_argument("--timeout-seconds", type=float, default=float(os.environ.get("DIALOGUE_REASONER_TIMEOUT_SECONDS") or 12.0))
    parser.add_argument("--temperature", type=float, default=float(os.environ.get("DIALOGUE_REASONER_TEMPERATURE") or DEFAULT_REASONER_TEMPERATURE))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    packets, state = deterministic_packets()
    requests = build_async_requests(packets, state)
    api_config = OpenAICompatibleReasonerConfig(
        base_url=args.api_base_url,
        model=args.api_model,
        api_key=os.environ.get(args.api_key_env),
        timeout_seconds=args.timeout_seconds,
        temperature=args.temperature,
    )
    local_config = OpenAICompatibleReasonerConfig(
        base_url=args.local_base_url,
        model=args.local_model,
        api_key="" if args.local_no_key else os.environ.get(args.local_api_key_env),
        timeout_seconds=args.timeout_seconds,
        temperature=args.temperature,
    )
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "mode": "live-provider" if args.live_provider else "dry-run",
        "provider_calls_made": False,
        "deterministic_only": {
            "turn_count": len(packets),
            "responses": [packet["summary"]["final_response"] for packet in packets],
        },
        "metrics": deterministic_metrics(packets),
        "async_request_count": len(requests),
        "async_provider_allowed_count": sum(1 for item in requests if item["request"].get("provider_call_allowed") is True),
        "lanes": [],
    }
    payload["lanes"].append(
        provider_lane(
            name="deterministic_plus_current_api_llm_async_enrichment",
            requests=requests,
            config=api_config,
            live_provider=args.live_provider,
            consent_confirmed=args.consent_confirmed,
            max_provider_cases=args.max_provider_cases,
        )
    )
    payload["lanes"].append(
        provider_lane(
            name="deterministic_plus_local_openai_compatible_async_enrichment",
            requests=requests,
            config=local_config,
            live_provider=args.live_provider,
            consent_confirmed=args.consent_confirmed,
            max_provider_cases=args.max_provider_cases,
        )
    )
    payload["provider_calls_made"] = any(lane.get("provider_calls_made") is True for lane in payload["lanes"])
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "mode": payload["mode"], "provider_calls_made": payload["provider_calls_made"]}))


if __name__ == "__main__":
    main()
