#!/usr/bin/env python3
from __future__ import annotations

import json
import importlib.util
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_ultravox_tunnel_sandbox_001 import TOOL_AUTH_TOKEN_NAME, build_temporary_tool_definition

CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_latency_optimization_config.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-LATENCY-OPTIMIZATION-BENCHMARK-001"
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
WARM_SCRIPT_PATH = ROOT / "scripts" / "run_ultravox_warm_session_latency_benchmark_001.py"


def load_warm_module() -> Any:
    spec = importlib.util.spec_from_file_location("run_ultravox_warm_session_latency_benchmark_001", WARM_SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load warm-session benchmark module spec.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


warm = load_warm_module()

CONFIRMED_SUPPORTED_PAYLOAD_KEYS_SENT = [
    "model",
    "temperature",
    "recordingEnabled",
    "firstSpeaker",
    "transcriptOptional",
    "initialOutputMedium",
    "joinTimeout",
    "maxDuration",
    "systemPrompt",
    "selectedTools",
    "metadata",
    "medium.serverWebSocket.inputSampleRate",
    "medium.serverWebSocket.outputSampleRate",
    "medium.serverWebSocket.clientBufferSizeMs",
    "medium.serverWebSocket.dataMessages.callStarted",
    "medium.serverWebSocket.dataMessages.transcript",
    "medium.serverWebSocket.dataMessages.callEvent",
    "medium.serverWebSocket.dataMessages.debug",
]


def compact_system_prompt() -> str:
    return (
        "You are the Ultravox voice interface for a synthetic, local-only sales-brain latency benchmark. "
        "Use the project_sales_brain_next_move tool for every buyer-facing answer. "
        "When the tool returns buyer_facing_response with verifier_status passed, speak only that response. "
        "Do not add explanation, product facts, CRM/email/calendar claims, or live-action claims. "
        "Keep the spoken answer to one or two short sentences. "
        "If the tool output is missing or blocked, ask one short clarification. "
        "This is not a phone call, not a microphone test, not live runtime, and not real customer data."
    )


def build_call_body(tool_url: str, tool_token: str, config: dict[str, Any]) -> dict[str, Any]:
    optimized = config.get("optimized_call_payload") if isinstance(config.get("optimized_call_payload"), dict) else {}
    body: dict[str, Any] = {
        "model": str(optimized.get("model") or "fixie-ai/ultravox"),
        "temperature": float(optimized.get("temperature", 0)),
        "recordingEnabled": False,
        "firstSpeaker": str(optimized.get("firstSpeaker") or "FIRST_SPEAKER_USER"),
        "transcriptOptional": False,
        "initialOutputMedium": str(optimized.get("initialOutputMedium") or "MESSAGE_MEDIUM_VOICE"),
        "medium": {
            "serverWebSocket": {
                "inputSampleRate": int(config["input_sample_rate"]),
                "outputSampleRate": int(config["output_sample_rate"]),
                "clientBufferSizeMs": int(optimized.get("serverWebSocketClientBufferSizeMs", 40)),
                "dataMessages": {
                    "callStarted": True,
                    "transcript": True,
                    "callEvent": True,
                    "debug": False,
                },
            }
        },
        "joinTimeout": str(optimized.get("joinTimeout") or "15s"),
        "maxDuration": str(optimized.get("maxDuration") or "75s"),
        "systemPrompt": compact_system_prompt(),
        "selectedTools": [
            {
                "temporaryTool": build_temporary_tool_definition(tool_url),
                "authTokens": {
                    TOOL_AUTH_TOKEN_NAME: tool_token,
                },
            }
        ],
        "metadata": {
            "project": "emotion-aware-ai-sales-agent",
            "milestone": "ULTRAVOX-LATENCY-OPTIMIZATION-BENCHMARK-001",
            "synthetic": "true",
            "realCustomerData": "false",
            "outboundPhoneCall": "false",
            "audioInput": "true",
            "manualAudioInput": "true",
            "latencyOptimizationBenchmark": "true",
            "liveWiring": "false",
        },
    }
    voice = optimized.get("voice")
    if isinstance(voice, str) and voice.strip():
        body["voice"] = voice.strip()
    return body


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def word_count(texts: list[Any]) -> int:
    return len(" ".join(str(text) for text in texts if text).split())


def post_process_result(result: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    latencies = warm.warm_latencies(result)
    p50 = warm.median(latencies)
    p90 = warm.percentile_nearest(latencies, 90.0) if len(latencies) >= 2 else None
    if result.get("run_status") == "warm_session_latency_measured":
        result["run_status"] = "latency_optimization_measured"
    result.update(
        {
            "evaluation_id": "ULTRAVOX-LATENCY-OPTIMIZATION-BENCHMARK-001",
            "phase": "4J8",
            "benchmark_id": config["benchmark_id"],
            "config_path": warm.rel(CONFIG_PATH),
            "max_provider_runs": int(config["max_provider_runs"]),
            "optimized_configuration_count": 1,
            "optimized_configuration_id": "conservative_prompt_first_speaker_buffer_001",
            "optimization_strategy": [
                "shorter benchmark-only system prompt",
                "one-or-two-sentence response instruction",
                "same project-owned HTTP sales-brain tool boundary",
                "FIRST_SPEAKER_USER to avoid initial agent greeting",
                "temperature 0",
                "serverWebSocket clientBufferSizeMs 40",
            ],
            "voice_selection_applied": False,
            "voice_selection_reason": "No confirmed built-in Ultravox voice ID/name is available locally; no voice was guessed.",
            "unsupported_parameters_sent_as_confirmed": False,
            "optimized_payload_keys_sent": CONFIRMED_SUPPORTED_PAYLOAD_KEYS_SENT,
            "confirmed_supported_payload_keys_sent": CONFIRMED_SUPPORTED_PAYLOAD_KEYS_SENT,
            "optimized_warm_latencies_seconds": latencies,
            "optimized_warm_measured_turn_count": len(latencies),
            "optimized_warm_p50_first_agent_audio_latency_seconds": p50,
            "optimized_warm_p90_first_agent_audio_latency_seconds": p90,
            "strong_live_target_met": bool(p50 is not None and p50 <= 2.0 and result.get("tool_boundary_enforced") is True),
            "early_demo_target_met": bool(p50 is not None and p50 <= 3.0 and result.get("tool_boundary_enforced") is True),
            "source_grounding": [
                *result.get("source_grounding", []),
                {
                    "url": "https://docs.ultravox.ai/api-reference/calls/calls-post",
                    "claim": "Create Call supports systemPrompt, temperature, model, voice, initialOutputMedium, selectedTools, firstSpeaker, medium.serverWebSocket, recordingEnabled, joinTimeout, and maxDuration.",
                },
                {
                    "url": "https://docs.ultravox.ai/agents/making-calls",
                    "claim": "Direct-call examples show overriding voice, temperature, model, selectedTools, and firstSpeakerSettings.",
                },
            ],
        }
    )
    for turn in result.get("turns", []):
        if isinstance(turn, dict):
            turn["agent_response_word_count"] = word_count(turn.get("agent_transcript_texts_sanitized", []))
            turn["response_length_recorded"] = bool(turn.get("agent_transcript_texts_sanitized"))
    return result


def render_report(result: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# ULTRAVOX-LATENCY-OPTIMIZATION-BENCHMARK-001",
            "",
            f"Run status: `{result['run_status']}`",
            f"Blocker: `{result['blocker']}`",
            "",
            "## Gates",
            f"Env file ignored: `{str(result['env_file_ignored']).lower()}`",
            f"API key present: `{str(result['api_key_present']).lower()}`",
            f"Tool token present: `{str(result['tool_token_present']).lower()}`",
            f"Prepared audio available: `{str(result['prepared_audio_available']).lower()}`",
            f"Repeated synthetic inputs used: `{str(result['repeated_synthetic_inputs_used']).lower()}`",
            "",
            "## Optimized Session",
            f"Provider call made: `{str(result['provider_call_made']).lower()}`",
            f"Session created: `{str(result['session_created']).lower()}`",
            f"WebSocket connected: `{str(result['websocket_connected']).lower()}`",
            f"Audio turns attempted: `{result['audio_turns_attempted']}`",
            f"Audio turns completed: `{result['audio_turns_completed']}`",
            f"Warm measured turn count: `{result['optimized_warm_measured_turn_count']}`",
            f"Voice selection applied: `{str(result['voice_selection_applied']).lower()}`",
            "",
            "## Latency",
            f"Optimized p50 first-agent-audio latency seconds: `{result['optimized_warm_p50_first_agent_audio_latency_seconds']}`",
            f"Optimized p90 first-agent-audio latency seconds: `{result['optimized_warm_p90_first_agent_audio_latency_seconds']}`",
            f"Measured warm latencies seconds: `{result['optimized_warm_latencies_seconds']}`",
            result["measurement_note"],
            "",
            "## Tool Boundary",
            f"Local HTTP tool request count: `{result['local_http_tool_request_count']}`",
            f"Tool call attempted: `{str(result['tool_call_attempted']).lower()}`",
            f"Tool call succeeded: `{str(result['tool_call_succeeded']).lower()}`",
            f"Tool boundary enforced: `{str(result['tool_boundary_enforced']).lower()}`",
            f"Product truth drift count: `{result['product_truth_drift_count']}`",
            f"Fake side effect count: `{result['fake_side_effect_count']}`",
            f"CRM/email/calendar claim count: `{result['crm_email_calendar_claim_count']}`",
            "",
            "## Boundaries",
            f"No new audio generated: `{str(result['no_new_audio_generation']).lower()}`",
            f"Raw audio stored public: `{str(result['raw_audio_stored_public']).lower()}`",
            f"Audio committed: `{str(result['audio_committed']).lower()}`",
            f"Live wiring allowed: `{str(result['live_wiring_allowed']).lower()}`",
            f"Production call allowed: `{str(result['production_call_allowed']).lower()}`",
            f"Runtime behavior changed: `{str(result['runtime_behavior_changed']).lower()}`",
            f"Response text changed: `{str(result['response_text_changed']).lower()}`",
            "",
        ]
    )


def main() -> None:
    warm.CONFIG_PATH = CONFIG_PATH
    warm.OUT_DIR = OUT_DIR
    warm.RESULT_PATH = RESULT_PATH
    warm.REPORT_PATH = REPORT_PATH
    warm.build_call_body = build_call_body
    config = warm.load_json(CONFIG_PATH)
    result = post_process_result(warm.build_result(), config)
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, render_report(result))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
