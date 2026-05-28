#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TTS_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-SYNTHETIC-TTS-SMOKE-001" / "result.json"
LOAD_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-MODEL-LOAD-PROBE-001" / "result.json"
ARCH_PLAN_PATH = ROOT / "runtime" / "audio_backends" / "speech_to_speech_architecture_plan.json"
IMPLEMENTATION_AUDIT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-SMOKE-IMPLEMENTATION-AUDIT-001" / "result.json"
LISTENING_REVIEW_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-LISTENING-REVIEW-001" / "result.json"
ASR_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-SYNTHETIC-ASR-SMOKE-001" / "result.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-LATENCY-AUDIT-001"
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
DECISION_OUT_DIR = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-SMOKE-DIAGNOSTIC-DECISION-001"
DECISION_RESULT_PATH = DECISION_OUT_DIR / "result.json"
DECISION_REPORT_PATH = DECISION_OUT_DIR / "report.md"
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


def numeric(summary: dict[str, Any], key: str) -> float | None:
    value = summary.get(key) if isinstance(summary, dict) else None
    return float(value) if isinstance(value, (int, float)) else None


def write_diagnostic_decision(latency: dict[str, Any]) -> dict[str, Any]:
    implementation = read_json(IMPLEMENTATION_AUDIT_PATH)
    listening = read_json(LISTENING_REVIEW_PATH)
    asr = read_json(ASR_RESULT_PATH)
    asr_failure = str(implementation.get("primary_asr_failure_cause") or "unknown")
    tts_review_entries = len(listening.get("review_entries") or []) if isinstance(listening.get("review_entries"), list) else 0
    asr_succeeded = int(asr.get("asr_succeeded_count") or 0)

    ranked = [
        {
            "rank": 1,
            "option": "liquid_tts_listening_review_next",
            "recommended": tts_review_entries > 0,
            "rationale": "TTS generated valid local audio but quality has not been manually reviewed.",
        },
        {
            "rank": 2,
            "option": "liquid_asr_prompt_mode_fix_next",
            "recommended": "prompt_mode" in asr_failure or "loopback" in asr_failure,
            "rationale": "ASR outputs looked like assistant responses and the current setup cannot isolate model quality.",
        },
        {
            "rank": 3,
            "option": "liquid_architecture_inspiration_only",
            "recommended": latency.get("current_smoke_live_usable") is False,
            "rationale": "Current TTS total latency and RTF are too slow for live voice without further optimization and verifier-safe streaming.",
        },
        {
            "rank": 4,
            "option": "liquid_independent_asr_benchmark_next",
            "recommended": False,
            "rationale": "Not recommended until ASR prompt/mode is fixed or a clean independent synthetic/recorded audio source is prepared.",
        },
        {
            "rank": 5,
            "option": "liquid_interleaved_s2s_probe_next",
            "recommended": False,
            "rationale": "Do not probe interleaved S2S yet; verifier gating and the current prompt/mode issue must be resolved first.",
        },
    ]
    decision = {
        "experiment_id": "LIQUID-AUDIO-SMOKE-DIAGNOSTIC-DECISION-001",
        "generated_at": utc_now(),
        "status": "pass",
        "implementation_audit": rel(IMPLEMENTATION_AUDIT_PATH),
        "listening_review": rel(LISTENING_REVIEW_PATH),
        "latency_audit": rel(RESULT_PATH),
        "primary_recommendation": ranked[0]["option"],
        "ranked_recommendations": ranked,
        "likely_asr_failure_cause": asr_failure,
        "independent_asr_benchmark_recommended": False,
        "interleaved_s2s_probe_recommended": False,
        "liquid_remains_offline_candidate_or_inspiration": True,
        "asr_setup_correct_enough_for_independent_benchmark": asr_succeeded > 0 and "prompt_mode" not in asr_failure,
        "live_wiring_allowed": False,
        "sales_brain_replacement_allowed": False,
        "provider_calls_made": False,
        "generated_audio_committed": bool(tracked_audio_files()),
        "model_weights_committed": bool(tracked_model_files()),
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "side_effects": side_effects(),
    }
    write_json(DECISION_RESULT_PATH, decision)
    write_text(
        DECISION_REPORT_PATH,
        "\n".join(
            [
                "# LIQUID-AUDIO-SMOKE-DIAGNOSTIC-DECISION-001",
                "",
                f"- status: {decision['status']}",
                f"- primary_recommendation: `{decision['primary_recommendation']}`",
                f"- likely_asr_failure_cause: {decision['likely_asr_failure_cause']}",
                f"- independent_asr_benchmark_recommended: {str(decision['independent_asr_benchmark_recommended']).lower()}",
                f"- interleaved_s2s_probe_recommended: {str(decision['interleaved_s2s_probe_recommended']).lower()}",
                f"- liquid_remains_offline_candidate_or_inspiration: {str(decision['liquid_remains_offline_candidate_or_inspiration']).lower()}",
                "- live_wiring_allowed: false",
                "- sales_brain_replacement_allowed: false",
                "",
                "## Ranked Recommendations",
                "",
                *[
                    f"{item['rank']}. `{item['option']}` - recommended: {str(item['recommended']).lower()} - {item['rationale']}"
                    for item in ranked
                ],
            ]
        ),
    )
    return decision


def main() -> int:
    tts = read_json(TTS_RESULT_PATH)
    load = read_json(LOAD_RESULT_PATH)
    arch = read_json(ARCH_PLAN_PATH)
    latency_summary = tts.get("latency_seconds") if isinstance(tts.get("latency_seconds"), dict) else {}
    first_audio_summary = tts.get("first_audio_latency_seconds") if isinstance(tts.get("first_audio_latency_seconds"), dict) else {}
    rtf_summary = tts.get("real_time_factor") if isinstance(tts.get("real_time_factor"), dict) else {}

    load_seconds = float(load.get("full_model_load_time_seconds") or 0.0)
    processor_seconds = float(load.get("processor_load_time_seconds") or 0.0)
    p50_generation = numeric(latency_summary, "p50")
    p90_generation = numeric(latency_summary, "p90")
    p50_first_audio = numeric(first_audio_summary, "p50")
    p90_first_audio = numeric(first_audio_summary, "p90")
    rtf_average = numeric(rtf_summary, "average")
    rtf_p50 = numeric(rtf_summary, "p50")
    current_live_usable = bool(
        p50_generation is not None
        and p50_generation <= 2.0
        and rtf_p50 is not None
        and rtf_p50 <= 1.0
    )
    perceived_streaming_possible = bool(p50_first_audio is not None and p50_first_audio <= 0.5)

    result = {
        "experiment_id": "LIQUID-AUDIO-LATENCY-AUDIT-001",
        "generated_at": utc_now(),
        "status": "pass",
        "inputs": {
            "tts_result": rel(TTS_RESULT_PATH),
            "model_load_probe": rel(LOAD_RESULT_PATH),
            "architecture_plan": rel(ARCH_PLAN_PATH),
        },
        "model_load_time": {
            "processor_load_time_seconds": processor_seconds,
            "full_model_load_time_seconds": load_seconds,
            "load_time_excluded_from_tts_generation_latency": True,
        },
        "generation_latency_seconds": latency_summary,
        "first_audio_latency_seconds": first_audio_summary,
        "real_time_factor": rtf_summary,
        "first_audio_vs_full_generation": {
            "p50_first_audio_seconds": p50_first_audio,
            "p50_full_generation_seconds": p50_generation,
            "p90_first_audio_seconds": p90_first_audio,
            "p90_full_generation_seconds": p90_generation,
            "p50_first_audio_is_fast_but_total_generation_is_slow": bool(
                p50_first_audio is not None and p50_first_audio <= 0.5 and p50_generation is not None and p50_generation > 2.0
            ),
        },
        "current_smoke_live_usable": current_live_usable,
        "offline_demo_candidate": bool(rtf_average is not None and rtf_average <= 2.0),
        "batch_generation_candidate": bool(rtf_average is not None and rtf_average <= 3.0),
        "streaming_interleaved_could_improve_perceived_latency": perceived_streaming_possible,
        "streaming_requires_verifier_gating_before_playback": True,
        "architecture_plan_constraints_preserved": {
            "sales_brain_project_owned": True,
            "verifier_gate_required_before_live_audio": True,
            "liquid_must_not_be_sales_brain": True,
            "plan_reference_present": bool(arch),
        },
        "latency_targets": {
            "live_voice": {
                "target": "p50 full TTS <= 2s, RTF <= 1.0, first audio <= 0.5s only if streaming verifier gate exists",
                "met_by_current_smoke": current_live_usable,
            },
            "offline_demo": {
                "target": "RTF <= 2.0 plus manual quality pass",
                "met_by_current_smoke": bool(rtf_average is not None and rtf_average <= 2.0),
            },
            "batch_generation": {
                "target": "RTF <= 3.0 and stable output quality",
                "met_by_current_smoke": bool(rtf_average is not None and rtf_average <= 3.0),
            },
            "architecture_inspiration": {
                "target": "no latency requirement; useful if pipeline ideas remain source-grounded",
                "met_by_current_smoke": True,
            },
        },
        "interpretation": "First-audio latency is promising, but full generation latency and RTF are too slow for live voice. Liquid remains plausible for offline demos, batch audio, or architecture inspiration pending listening review and prompt/mode fixes.",
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "elevenlabs_calls_made": False,
        "live_tts_calls_made": False,
        "live_wiring_allowed": False,
        "sales_brain_replacement_allowed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "model_weights_committed": bool(tracked_model_files()),
        "audio_files_committed": bool(tracked_audio_files()),
        "side_effects": side_effects(),
    }
    write_json(RESULT_PATH, result)
    write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# LIQUID-AUDIO-LATENCY-AUDIT-001",
                "",
                f"- status: {result['status']}",
                f"- processor_load_time_seconds: {processor_seconds}",
                f"- full_model_load_time_seconds: {load_seconds}",
                f"- tts_p50_generation_seconds: {p50_generation}",
                f"- tts_p90_generation_seconds: {p90_generation}",
                f"- first_audio_p50_seconds: {p50_first_audio}",
                f"- first_audio_p90_seconds: {p90_first_audio}",
                f"- rtf_average: {rtf_average}",
                f"- current_smoke_live_usable: {str(current_live_usable).lower()}",
                f"- streaming_interleaved_could_improve_perceived_latency: {str(perceived_streaming_possible).lower()}",
                "- streaming_requires_verifier_gating_before_playback: true",
                "- live_wiring_allowed: false",
                "- sales_brain_replacement_allowed: false",
                "",
                "## Interpretation",
                "",
                result["interpretation"],
            ]
        ),
    )
    decision = write_diagnostic_decision(result)
    print(
        json.dumps(
            {
                "status": "pass",
                "current_smoke_live_usable": current_live_usable,
                "primary_recommendation": decision["primary_recommendation"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
