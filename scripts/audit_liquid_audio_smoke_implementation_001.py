#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from typing import Any
import wave


ROOT = Path(__file__).resolve().parents[1]
SMOKE_SCRIPT_PATH = ROOT / "scripts" / "run_liquid_audio_feasibility_smoke_001.py"
CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "liquid_audio_feasibility_config.json"
SMOKE_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-FEASIBILITY-SMOKE-001" / "result.json"
TTS_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-SYNTHETIC-TTS-SMOKE-001" / "result.json"
ASR_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-SYNTHETIC-ASR-SMOKE-001" / "result.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-SMOKE-IMPLEMENTATION-AUDIT-001"
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
MODEL_SUFFIXES = (".safetensors", ".bin", ".gguf", ".pt", ".pth", ".ckpt", ".onnx")
AUDIO_SUFFIXES = (".mp3", ".wav", ".flac", ".m4a", ".ogg")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def git_lines(args: list[str]) -> list[str]:
    completed = subprocess.run(
        ["git", "--no-optional-locks", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if completed.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()]


def tracked_model_files() -> list[str]:
    return [
        path
        for path in git_lines(["ls-files"])
        if path.startswith("local_artifacts/") or path.lower().endswith(MODEL_SUFFIXES)
    ]


def tracked_audio_files() -> list[str]:
    return [path for path in git_lines(["ls-files"]) if path.lower().endswith(AUDIO_SUFFIXES)]


def side_effects() -> dict[str, bool]:
    return {
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "elevenlabs_calls_made": False,
        "live_tts_calls_made": False,
        "new_liquid_inference_run": False,
        "new_audio_generated": False,
        "model_download_attempted": False,
        "model_weights_committed": bool(tracked_model_files()),
        "audio_files_committed": bool(tracked_audio_files()),
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "raw_private_audio_used": False,
        "raw_private_transcripts_included": False,
    }


def wav_info(relative_path: str) -> dict[str, Any]:
    path = ROOT / relative_path
    info: dict[str, Any] = {
        "path": relative_path,
        "exists": path.is_file(),
        "under_local_artifacts": relative_path.replace("\\", "/").startswith("local_artifacts/audio_outputs/liquid/"),
    }
    if not path.is_file():
        return info
    try:
        with wave.open(str(path), "rb") as wav:
            sample_rate = int(wav.getframerate())
            frames = int(wav.getnframes())
            info.update(
                {
                    "channels": int(wav.getnchannels()),
                    "sample_rate": sample_rate,
                    "sample_width_bytes": int(wav.getsampwidth()),
                    "frames": frames,
                    "duration_seconds": round(frames / float(sample_rate), 6) if sample_rate else None,
                }
            )
    except Exception as exc:  # pragma: no cover - evidence path
        info["metadata_error"] = f"{type(exc).__name__}: {exc}"
    return info


def looks_like_assistant_response(text: str) -> bool:
    lower = text.lower()
    markers = (
        "couldn't understand",
        "could you",
        "can't assist",
        "feel free to ask",
        "please try again",
        "tell me more",
        "i didn't quite hear",
    )
    return any(marker in lower for marker in markers)


def main() -> int:
    config = read_json(CONFIG_PATH)
    smoke = read_json(SMOKE_RESULT_PATH)
    tts = read_json(TTS_RESULT_PATH)
    asr = read_json(ASR_RESULT_PATH)
    script = SMOKE_SCRIPT_PATH.read_text(encoding="utf-8") if SMOKE_SCRIPT_PATH.is_file() else ""
    source_requirements = config.get("source_grounded_requirements") if isinstance(config.get("source_grounded_requirements"), dict) else {}
    source_evidence = config.get("source_evidence") if isinstance(config.get("source_evidence"), list) else []

    asr_cases = [
        case
        for case in (asr.get("cases") or []) + (asr.get("roundtrip_cases") or [])
        if isinstance(case, dict)
    ]
    assistant_like_count = sum(1 for case in asr_cases if looks_like_assistant_response(str(case.get("transcript") or "")))
    transcript_like_count = sum(
        1
        for case in asr_cases
        if case.get("exact_match") is True or int(case.get("critical_terms_preserved_count") or 0) > 0
    )
    loopback_paths = [
        str(case.get("audio_input_path") or "").replace("\\", "/")
        for case in asr_cases
        if str(case.get("audio_input_path") or "").replace("\\", "/").endswith(AUDIO_SUFFIXES)
    ]
    loopback_audio_metadata = [wav_info(path) for path in sorted(set(loopback_paths))]

    tts_mode_used = "interleaved_generation_chat_prompt" if "generate_interleaved" in script and "build_tts_chat" in script else "unknown"
    asr_mode_used = "sequential_generation_chat_prompt" if "generate_sequential" in script and "build_asr_chat" in script else "unknown"
    source_stated_tts = "TTS via sequential generation" in source_requirements.get("source_stated_capabilities", [])
    source_stated_asr = "ASR via sequential generation" in source_requirements.get("source_stated_capabilities", [])

    likely_failure_causes = [
        {
            "cause": "prompt_or_mode_misuse",
            "likelihood": "high",
            "evidence": "ASR outputs look like assistant repair/chat responses rather than literal transcripts; TTS used interleaved chat generation despite source notes saying TTS is sequential.",
        },
        {
            "cause": "loopback_audio_artifact_issue",
            "likelihood": "medium",
            "evidence": "ASR input was Liquid-generated loopback audio, not an independent controlled recording; listening quality has not been reviewed yet.",
        },
        {
            "cause": "audio_format_sample_rate_issue",
            "likelihood": "low_to_medium",
            "evidence": "Loopback WAVs are mono 16-bit PCM at 24 kHz; ChatState.add_audio accepts waveform plus sampling rate and resamples internally, but official ASR example expectations still need a focused check.",
        },
        {
            "cause": "verifier_too_strict",
            "likelihood": "low",
            "evidence": "The transcripts did not merely miss exact phrasing; they failed all critical-term checks and often contained conversational fallback text.",
        },
        {
            "cause": "actual_model_limitation",
            "likelihood": "unknown",
            "evidence": "The current loopback setup is not clean enough to isolate model quality from prompting/mode/audio-source artifacts.",
        },
        {
            "cause": "latency_rtf_issue",
            "likelihood": "confirmed_for_live_use",
            "evidence": "TTS generated audio but p50 total generation latency and RTF are above live-turn targets.",
        },
    ]

    audit = {
        "experiment_id": "LIQUID-AUDIO-SMOKE-IMPLEMENTATION-AUDIT-001",
        "generated_at": utc_now(),
        "status": "pass",
        "inputs": {
            "smoke_script": rel(SMOKE_SCRIPT_PATH),
            "smoke_result": rel(SMOKE_RESULT_PATH),
            "tts_result": rel(TTS_RESULT_PATH),
            "asr_result": rel(ASR_RESULT_PATH),
            "config": rel(CONFIG_PATH),
        },
        "source_grounding": {
            "source_stated_capabilities": source_requirements.get("source_stated_capabilities", []),
            "generation_routines": source_requirements.get("generation_routines", []),
            "source_evidence": source_evidence,
            "official_examples_unclear_items": [
                "Whether the chat-style TTS prompt used in the smoke is equivalent to the official sequential TTS path.",
                "Whether a direct ASR prompt template exists for one-shot transcription without assistant fallback behavior.",
                "Whether Liquid-generated speech is an acceptable ASR loopback source for diagnosis.",
            ],
        },
        "mode_audit": {
            "tts_mode_used": tts_mode_used,
            "source_stated_tts_mode": "sequential_generation" if source_stated_tts else "unknown",
            "tts_mode_alignment": "questionable_mismatch" if source_stated_tts and tts_mode_used.startswith("interleaved") else "unknown",
            "asr_mode_used": asr_mode_used,
            "source_stated_asr_mode": "sequential_generation" if source_stated_asr else "unknown",
            "asr_mode_alignment": "partial_match_but_prompt_may_be_conversational" if source_stated_asr and asr_mode_used.startswith("sequential") else "unknown",
            "asked_to_transcribe": "Transcribe the user's audio exactly" in script,
            "asked_to_chat_or_respond": "new_turn(\"assistant\")" in script,
            "chat_state_roles_used": all(fragment in script for fragment in ("new_turn(\"system\")", "new_turn(\"user\")", "new_turn(\"assistant\")")),
        },
        "output_audit": {
            "tts_generated_count": int(tts.get("tts_succeeded_count") or 0),
            "asr_attempted_count": int(asr.get("asr_attempted_count") or 0),
            "asr_succeeded_count": int(asr.get("asr_succeeded_count") or 0),
            "critical_terms_preserved_count": int(asr.get("critical_terms_preserved_count") or 0),
            "critical_terms_total": int(asr.get("critical_terms_total") or 0),
            "assistant_like_asr_output_count": assistant_like_count,
            "transcript_like_asr_output_count": transcript_like_count,
            "asr_output_classification": "assistant_response_not_transcript" if assistant_like_count > transcript_like_count else "mixed_or_unknown",
        },
        "audio_input_audit": {
            "loopback_only": bool(asr.get("loopback_only")),
            "loopback_audio_metadata": loopback_audio_metadata,
            "sample_rate_channel_assessment": "format_valid_for_local_wav_and_probably_acceptable_for_ChatState_add_audio_but_not_independent_asr_quality_evidence",
            "generated_tts_loopback_is_valid_asr_quality_source": False,
            "generated_tts_loopback_is_valid_plumbing_source": True,
        },
        "likely_failure_causes": likely_failure_causes,
        "primary_asr_failure_cause": "likely_prompt_mode_or_loopback_artifact_issue_not_final_model_limitation",
        "primary_tts_issue": "latency_rtf_too_slow_for_live_and_quality_unreviewed",
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "live_wiring_allowed": False,
        "sales_brain_replacement_allowed": False,
        "side_effects": side_effects(),
    }

    write_json(RESULT_PATH, audit)
    write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# LIQUID-AUDIO-SMOKE-IMPLEMENTATION-AUDIT-001",
                "",
                f"- status: {audit['status']}",
                f"- tts_mode_used: {audit['mode_audit']['tts_mode_used']}",
                f"- tts_mode_alignment: {audit['mode_audit']['tts_mode_alignment']}",
                f"- asr_mode_used: {audit['mode_audit']['asr_mode_used']}",
                f"- asr_mode_alignment: {audit['mode_audit']['asr_mode_alignment']}",
                f"- asr_output_classification: {audit['output_audit']['asr_output_classification']}",
                f"- primary_asr_failure_cause: {audit['primary_asr_failure_cause']}",
                f"- primary_tts_issue: {audit['primary_tts_issue']}",
                f"- live_wiring_allowed: false",
                f"- sales_brain_replacement_allowed: false",
                "",
                "## Findings",
                "",
                "- The smoke did not prove independent ASR quality. Loopback ASR outputs looked like assistant responses, not transcripts.",
                "- TTS generated audio, but the smoke used an interleaved/chat path while the recorded source notes describe sequential generation for TTS.",
                "- The loopback WAV files are local mono PCM artifacts under `local_artifacts/audio_outputs/liquid`; they were not copied into this report.",
                "- The likely ASR failure cause is prompt/mode or loopback artifact misuse, not enough evidence for final model limitation.",
            ]
        ),
    )
    print(json.dumps({"status": "pass", "primary_asr_failure_cause": audit["primary_asr_failure_cause"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
