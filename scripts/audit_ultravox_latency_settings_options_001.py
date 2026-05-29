#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "ultravox_latency_optimization_config.json"
VOICE_IDS_PATH = ROOT / "config" / "local" / "voice_ids.json"
SCRIPT_PATHS = [
    ROOT / "scripts" / "run_ultravox_warm_session_latency_benchmark_001.py",
    ROOT / "scripts" / "run_ultravox_websocket_audio_sandbox_001.py",
    ROOT / "scripts" / "run_ultravox_003_synthetic_audio_turn.py",
]
OUT_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-LATENCY-SETTINGS-OPTIONS-001"
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"

OFFICIAL_SOURCES = [
    {
        "url": "https://docs.ultravox.ai/api-reference/calls/calls-post",
        "used_for": [
            "systemPrompt",
            "temperature",
            "model",
            "voice",
            "initialOutputMedium",
            "selectedTools",
            "firstSpeaker",
            "firstSpeakerSettings",
            "serverWebSocket",
            "recordingEnabled",
            "joinTimeout",
            "maxDuration",
        ],
    },
    {
        "url": "https://docs.ultravox.ai/api-reference/calls/calls-stages-get",
        "used_for": ["stage fields such as temperature, model, systemPrompt, voice, externalVoice, voiceOverrides"],
    },
    {
        "url": "https://docs.ultravox.ai/agents/making-calls",
        "used_for": ["direct call override examples for voice, temperature, model, firstSpeakerSettings, selectedTools"],
    },
    {
        "url": "https://docs.ultravox.ai/voices/overview",
        "used_for": ["built-in voices, voice cloning, and bring-your-own TTS option categories"],
    },
]


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def current_payload_keys() -> list[str]:
    candidate_keys = [
        "model",
        "recordingEnabled",
        "firstSpeaker",
        "firstSpeakerSettings",
        "transcriptOptional",
        "initialOutputMedium",
        "languageHint",
        "joinTimeout",
        "maxDuration",
        "systemPrompt",
        "selectedTools",
        "medium",
        "serverWebSocket",
        "inputSampleRate",
        "outputSampleRate",
        "clientBufferSizeMs",
        "dataMessages",
        "metadata",
        "voice",
        "temperature",
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in SCRIPT_PATHS if path.is_file())
    return [key for key in candidate_keys if f'"{key}"' in text]


def local_voice_availability() -> dict[str, Any]:
    voice_ids = load_json(VOICE_IDS_PATH)
    providers = sorted(key for key in voice_ids if isinstance(voice_ids.get(key), dict))
    return {
        "voice_ids_file_present": VOICE_IDS_PATH.is_file(),
        "local_voice_provider_groups": providers,
        "ultravox_builtin_voice_value_available": False,
        "note": "Local voice_ids.json contains provider-specific voice IDs, but no confirmed built-in Ultravox voice ID/name for the hosted sandbox.",
    }


def option(option_id: str, classification: str, evidence: str, *, sent: bool, payload_keys: list[str] | None = None, value: Any = None, risk: str | None = None) -> dict[str, Any]:
    item: dict[str, Any] = {
        "option_id": option_id,
        "classification": classification,
        "sent_in_optimized_payload": sent,
        "payload_keys": payload_keys or [],
        "evidence": evidence,
    }
    if value is not None:
        item["optimized_value"] = value
    if risk:
        item["risk"] = risk
    return item


def build_result() -> dict[str, Any]:
    config = load_json(CONFIG_PATH)
    payload = config.get("optimized_call_payload") if isinstance(config.get("optimized_call_payload"), dict) else {}
    keys_seen = current_payload_keys()
    voice_info = local_voice_availability()
    options = [
        option(
            "system_prompt_brevity",
            "supported_now",
            "Create Call supports systemPrompt; current scripts already build the call prompt locally.",
            sent=True,
            payload_keys=["systemPrompt"],
        ),
        option(
            "voice_selection",
            "supported_but_needs_value",
            "Create Call supports voice by ID or unique name, and Voices docs describe built-in voices, but no known Ultravox voice value exists in local config.",
            sent=False,
            payload_keys=["voice"],
            risk="Guessing a voice could break the one allowed provider run.",
        ),
        option(
            "initial_output_medium",
            "supported_now",
            "Create Call supports initialOutputMedium with voice/text choices; current scripts use voice for audio latency measurement.",
            sent=True,
            payload_keys=["initialOutputMedium"],
            value=payload.get("initialOutputMedium"),
        ),
        option(
            "output_medium_controls",
            "supported_now",
            "Create Call supports medium.serverWebSocket and initialOutputMedium; the benchmark keeps serverWebSocket voice output.",
            sent=True,
            payload_keys=["medium", "serverWebSocket", "initialOutputMedium"],
        ),
        option(
            "server_websocket_client_buffer",
            "supported_now",
            "Create Call serverWebSocket includes clientBufferSizeMs. The docs confirm the field, but not a generic latency guarantee.",
            sent=True,
            payload_keys=["medium.serverWebSocket.clientBufferSizeMs"],
            value=payload.get("serverWebSocketClientBufferSizeMs"),
        ),
        option(
            "model",
            "supported_now",
            "Create Call supports model; current local Ultravox scripts already send fixie-ai/ultravox.",
            sent=True,
            payload_keys=["model"],
            value=payload.get("model"),
        ),
        option(
            "temperature",
            "supported_now",
            "Create Call supports temperature between 0 and 1; optimized run uses deterministic temperature 0.",
            sent=True,
            payload_keys=["temperature"],
            value=payload.get("temperature"),
        ),
        option(
            "prompt_call_stage_simplification",
            "supported_now",
            "Create Call supports systemPrompt and selectedTools in the first stage; prompt complexity can be reduced without moving sales logic into Ultravox.",
            sent=True,
            payload_keys=["systemPrompt", "selectedTools"],
        ),
        option(
            "first_message_behavior",
            "supported_now",
            "Create Call supports firstSpeaker and firstSpeakerSettings. Existing local scripts have used FIRST_SPEAKER_USER for audio-turn tests.",
            sent=True,
            payload_keys=["firstSpeaker"],
            value=payload.get("firstSpeaker"),
        ),
        option(
            "response_length_control",
            "supported_now",
            "No max-output-token field was confirmed for Create Call; response length is constrained by prompt wording only.",
            sent=True,
            payload_keys=["systemPrompt"],
            value=payload.get("response_length_instruction"),
        ),
        option(
            "tool_choice_wording",
            "supported_now",
            "Create Call supports selectedTools. The optimized run keeps the same project-owned temporary HTTP tool and shortens wording around using it.",
            sent=True,
            payload_keys=["selectedTools"],
        ),
        option(
            "tool_declaration",
            "supported_now",
            "Create Call selectedTools supports temporary tools; current scripts already route to the local project sales-brain endpoint.",
            sent=True,
            payload_keys=["selectedTools.temporaryTool"],
        ),
        option(
            "voice_overrides",
            "supported_but_needs_value",
            "Create Call documents voiceOverrides only when a voice is set. The sandbox has no known voice value, so overrides are not sent.",
            sent=False,
            payload_keys=["voiceOverrides"],
        ),
        option(
            "external_voice",
            "not_safe",
            "External voice providers would require separate provider keys and could trigger non-Ultravox TTS usage, which this phase forbids.",
            sent=False,
            payload_keys=["externalVoice"],
        ),
        option(
            "low_latency_mode",
            "unknown",
            "No documented generic low-latency mode was confirmed in official Create Call or call-stage docs.",
            sent=False,
            payload_keys=[],
        ),
    ]
    sent_keys = sorted({key for item in options if item["sent_in_optimized_payload"] for key in item["payload_keys"]})
    return {
        "evaluation_id": "ULTRAVOX-LATENCY-SETTINGS-OPTIONS-001",
        "phase": "4J8",
        "config_path": rel(CONFIG_PATH),
        "provider_call_made": False,
        "docs_fetch_performed": False,
        "official_sources": OFFICIAL_SOURCES,
        "repo_files_inspected": [rel(path) for path in SCRIPT_PATHS if path.is_file()] + ([rel(VOICE_IDS_PATH)] if VOICE_IDS_PATH.is_file() else []),
        "current_scripts_payload_keys_seen": keys_seen,
        "voice_availability": voice_info,
        "voice_change_possible_in_current_sandbox": False,
        "prompt_brevity_change_possible": True,
        "response_length_constraints_supported": "prompt_only",
        "tool_prompt_complexity_reduction_likely_to_help": "plausible_not_proven",
        "documented_low_latency_mode": "unknown",
        "unsupported_parameters_sent_as_confirmed": False,
        "optimized_payload_keys_considered_supported": sent_keys,
        "options": options,
    }


def render_report(result: dict[str, Any]) -> str:
    option_lines = [
        f"- `{item['option_id']}`: `{item['classification']}`; sent `{str(item['sent_in_optimized_payload']).lower()}`"
        for item in result["options"]
    ]
    return "\n".join(
        [
            "# ULTRAVOX-LATENCY-SETTINGS-OPTIONS-001",
            "",
            f"Provider call made: `{str(result['provider_call_made']).lower()}`",
            f"Docs fetch performed: `{str(result['docs_fetch_performed']).lower()}`",
            f"Voice change possible in current sandbox: `{str(result['voice_change_possible_in_current_sandbox']).lower()}`",
            f"Prompt brevity change possible: `{str(result['prompt_brevity_change_possible']).lower()}`",
            f"Response length constraints: `{result['response_length_constraints_supported']}`",
            f"Low-latency mode: `{result['documented_low_latency_mode']}`",
            f"Unsupported parameters sent as confirmed: `{str(result['unsupported_parameters_sent_as_confirmed']).lower()}`",
            "",
            "## Supported Settings",
            *option_lines,
            "",
            "## Official Sources",
            *[f"- {source['url']}" for source in result["official_sources"]],
            "",
        ]
    )


def main() -> None:
    result = build_result()
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, render_report(result))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
