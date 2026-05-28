#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from difflib import SequenceMatcher
import gc
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import traceback
from typing import Any
import wave


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "liquid_audio_feasibility_config.json"
ENV_CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "liquid_audio_env_config.json"
MODEL_CONFIG_PATH = ROOT / "runtime" / "audio_backends" / "liquid_audio_model_probe_config.json"
ENV_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-ENVIRONMENT-PROBE-001" / "result.json"
SETUP_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-ENV-SETUP-001" / "result.json"
MODEL_LOAD_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-MODEL-LOAD-PROBE-001" / "result.json"

SMOKE_OUT_DIR = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-FEASIBILITY-SMOKE-001"
SMOKE_RESULT_PATH = SMOKE_OUT_DIR / "result.json"
SMOKE_REPORT_PATH = SMOKE_OUT_DIR / "report.md"
LEGACY_DECISION_OUT_DIR = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-FEASIBILITY-DECISION-001"
LEGACY_DECISION_RESULT_PATH = LEGACY_DECISION_OUT_DIR / "result.json"
LEGACY_DECISION_REPORT_PATH = LEGACY_DECISION_OUT_DIR / "report.md"

TTS_OUT_DIR = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-SYNTHETIC-TTS-SMOKE-001"
TTS_RESULT_PATH = TTS_OUT_DIR / "result.json"
TTS_REPORT_PATH = TTS_OUT_DIR / "report.md"
ASR_OUT_DIR = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-SYNTHETIC-ASR-SMOKE-001"
ASR_RESULT_PATH = ASR_OUT_DIR / "result.json"
ASR_REPORT_PATH = ASR_OUT_DIR / "report.md"
DECISION_OUT_DIR = ROOT / "research" / "experiments" / "generated" / "LIQUID-AUDIO-SMOKE-DECISION-001"
DECISION_RESULT_PATH = DECISION_OUT_DIR / "result.json"
DECISION_REPORT_PATH = DECISION_OUT_DIR / "report.md"

MODEL_SUFFIXES = (".safetensors", ".bin", ".gguf", ".pt", ".pth", ".ckpt", ".onnx")
AUDIO_SUFFIXES = (".mp3", ".wav", ".flac", ".m4a", ".ogg")
SAMPLE_RATE = 24_000
MAX_TTS_TOKENS = 420
MAX_ASR_TOKENS = 160

TTS_UTTERANCES = [
    "Just so I answer the right thing, are you asking about the plans themselves or which one fits your use?",
    "Got it \u2014 coding workflow and voice. Are you using it lightly, moderately, or heavily?",
    "I heard something like Claude there \u2014 are you comparing ChatGPT with Claude, or did I catch that wrong?",
    "If you are using it heavily for coding, Pro is the safer plan to compare, while Plus is the lower-cost starting point.",
    "Sounds good. Start from the official ChatGPT plans page, and if you are unsure, start lower and move up only if you need more headroom.",
]

ASR_PHRASES = [
    "ChatGPT",
    "ChatGPT and other AI tools",
    "Claude",
    "coding and voice",
    "Free Plus Pro Business Enterprise",
    "I am by myself, not a team",
    "I use ChatGPT or maybe Claude",
]

ROUNDTRIP_PHRASES = [
    "ChatGPT",
    "coding and voice",
    "I am by myself, not a team",
]

REQUIRED_INFERENCE_GATES = {
    "ENABLE_LOCAL_AUDIO_EXPERIMENT": "1",
    "LOCAL_LIQUID_AUDIO_ENABLED": "true",
    "LOCAL_LIQUID_ALLOW_MODEL_LOAD": "1",
    "LOCAL_LIQUID_ALLOW_INFERENCE": "1",
}


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


def env_flag(name: str, expected: str) -> bool:
    return str(os.getenv(name) or "").strip().lower() == expected.strip().lower()


def gate_report() -> dict[str, dict[str, Any]]:
    return {
        name: {
            "expected": expected,
            "actual": os.getenv(name, ""),
            "enabled": env_flag(name, expected),
        }
        for name, expected in REQUIRED_INFERENCE_GATES.items()
    }


def gates_enabled() -> bool:
    return all(env_flag(name, expected) for name, expected in REQUIRED_INFERENCE_GATES.items())


def model_files(model_path: Path) -> list[str]:
    if not model_path.exists():
        return []
    return [
        rel(path)
        for path in model_path.rglob("*")
        if path.is_file() and path.suffix.lower() in MODEL_SUFFIXES
    ][:50]


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


def tracked_audio_files() -> list[str]:
    tracked = git_lines(["ls-files"])
    return [path for path in tracked if path.lower().endswith(AUDIO_SUFFIXES)]


def tracked_model_files() -> list[str]:
    tracked = git_lines(["ls-files"])
    return [
        path
        for path in tracked
        if path.startswith("local_artifacts/") or path.lower().endswith(MODEL_SUFFIXES)
    ]


def path_is_under(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def side_effects(*, allowed_local_audio_generation: bool = False, audio_files_generated: bool = False) -> dict[str, bool]:
    return {
        "model_download_attempted": False,
        "model_downloads_performed": False,
        "model_weights_committed": bool(tracked_model_files()),
        "audio_files_generated": bool(audio_files_generated),
        "allowed_local_audio_generation": bool(allowed_local_audio_generation),
        "audio_files_committed": bool(tracked_audio_files()),
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "elevenlabs_calls_made": False,
        "live_tts_calls_made": False,
        "local_model_generation_made": bool(audio_files_generated),
        "ollama_generation_made": False,
        "training_performed": False,
        "live_runtime_wiring_changed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "raw_private_audio_used": False,
        "raw_private_transcripts_included": False,
        "sales_brain_replacement_allowed": False,
        "live_wiring_allowed": False,
    }


def audio_metadata(path: Path, torchaudio_module: Any | None = None, torch_module: Any | None = None) -> dict[str, Any]:
    if not path.is_file():
        return {}
    meta: dict[str, Any] = {"output_audio_path": rel(path)}
    meta["file_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    try:
        with wave.open(str(path), "rb") as wav:
            channels = int(wav.getnchannels())
            sample_rate = int(wav.getframerate())
            frames = int(wav.getnframes())
            pcm = wav.readframes(frames)
        meta.update(
            {
                "sample_rate": sample_rate,
                "channels": channels,
                "frames": frames,
                "duration_seconds": round(frames / float(sample_rate), 6) if sample_rate else None,
                "waveform_hash": hashlib.sha256(pcm).hexdigest(),
            }
        )
        if torch_module.cuda.is_available():
            meta["peak_gpu_memory_reserved"] = int(torch_module.cuda.max_memory_reserved())
    except Exception as exc:  # pragma: no cover - evidence path
        meta["metadata_error"] = f"{type(exc).__name__}: {exc}"
    return meta


def save_wav_pcm16(path: Path, waveform: Any, sample_rate: int, torch: Any) -> None:
    if waveform.dim() == 3:
        waveform = waveform.squeeze(0)
    if waveform.dim() == 1:
        waveform = waveform.unsqueeze(0)
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)
    pcm = waveform.squeeze(0).detach().cpu().clamp(-1.0, 1.0).mul(32767.0).to(torch.int16).contiguous()
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm.numpy().tobytes())


def load_wav_tensor(path: Path, torch: Any) -> tuple[Any, int]:
    with wave.open(str(path), "rb") as wav:
        channels = int(wav.getnchannels())
        sample_rate = int(wav.getframerate())
        sample_width = int(wav.getsampwidth())
        frames = int(wav.getnframes())
        pcm = wav.readframes(frames)
    if sample_width != 2:
        raise RuntimeError(f"Only 16-bit PCM WAV is supported by the smoke loader, got sample_width={sample_width}.")
    samples = torch.frombuffer(bytearray(pcm), dtype=torch.int16).to(torch.float32).div(32768.0)
    if channels > 1:
        samples = samples.view(-1, channels).mean(dim=1)
    return samples.unsqueeze(0), sample_rate


def normalize_text(text: str) -> str:
    compact = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    compact = compact.replace("chat gpt", "chatgpt")
    return re.sub(r"\s+", " ", compact)


def fuzzy_score(target: str, transcript: str) -> float:
    return round(SequenceMatcher(None, normalize_text(target), normalize_text(transcript)).ratio(), 4)


def critical_term_metrics(target_phrase: str, transcript: str) -> dict[str, Any]:
    target = normalize_text(target_phrase)
    observed = normalize_text(transcript)
    terms: dict[str, bool | None] = {
        "ChatGPT": None,
        "Claude": None,
        "coding": None,
        "voice": None,
        "not team": None,
        "and/or": None,
    }
    if "chatgpt" in target:
        terms["ChatGPT"] = "chatgpt" in observed
    if "claude" in target:
        terms["Claude"] = "claude" in observed
    if "coding" in target:
        terms["coding"] = "coding" in observed
    if "voice" in target:
        terms["voice"] = "voice" in observed
    if "not a team" in target or ("not" in target and "team" in target):
        terms["not team"] = ("not" in observed and "team" in observed) or "by myself" in observed
    if " and " in f" {target} " or " or " in f" {target} ":
        expected_words = {word for word in ("and", "or") if f" {word} " in f" {target} "}
        terms["and/or"] = all(f" {word} " in f" {observed} " for word in expected_words)
    present = {key: value for key, value in terms.items() if value is not None}
    return {
        "critical_term_preserved": present,
        "critical_terms_checked": sorted(present),
        "critical_terms_preserved_count": sum(1 for value in present.values() if value is True),
        "critical_terms_total": len(present),
    }


def decode_text_tokens(processor: Any, tokens: list[Any]) -> str:
    if not tokens:
        return ""
    token_ids: list[int] = []
    for token in tokens:
        try:
            token_ids.append(int(token.detach().cpu().view(-1)[0].item()))
        except Exception:
            continue
    if not token_ids:
        return ""
    try:
        return str(processor.text.decode(token_ids, skip_special_tokens=True)).strip()
    except TypeError:
        return str(processor.text.decode(token_ids)).strip()


def split_generated_tokens(tokens: list[Any]) -> tuple[list[Any], list[Any]]:
    text_tokens: list[Any] = []
    audio_frames: list[Any] = []
    for token in tokens:
        try:
            if token.dim() == 0 or token.numel() == 1:
                text_tokens.append(token)
                continue
            if token.dim() == 1 and token.numel() >= 8:
                if int(token.detach().cpu().view(-1)[0].item()) == 2048:
                    continue
                audio_frames.append(token[:8])
        except Exception:
            continue
    return text_tokens, audio_frames


def load_liquid(model_path: Path) -> dict[str, Any]:
    import torch
    import torchaudio
    from liquid_audio import LFM2AudioModel, LFM2AudioProcessor
    from liquid_audio.processor import ChatState

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.bfloat16 if device == "cuda" else torch.float32
    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()
    start = time.perf_counter()
    processor = LFM2AudioProcessor.from_pretrained(model_path, device=device)
    processor_load_time = time.perf_counter() - start
    start = time.perf_counter()
    model = LFM2AudioModel.from_pretrained(model_path, dtype=dtype, device=device)
    model_load_time = time.perf_counter() - start
    model.eval()
    return {
        "torch": torch,
        "torchaudio": torchaudio,
        "ChatState": ChatState,
        "processor": processor,
        "model": model,
        "device": device,
        "dtype": str(dtype).replace("torch.", ""),
        "processor_load_time_seconds": round(processor_load_time, 6),
        "model_load_time_seconds": round(model_load_time, 6),
    }


def unload_liquid(resources: dict[str, Any]) -> None:
    torch = resources.get("torch")
    for key in ("model", "processor"):
        resources[key] = None
    gc.collect()
    if torch is not None and torch.cuda.is_available():
        torch.cuda.empty_cache()


def gpu_metrics(torch: Any) -> dict[str, Any]:
    metrics = {
        "cuda_available": bool(torch.cuda.is_available()),
        "peak_gpu_memory_reserved": None,
        "max_gpu_memory_allocated": None,
        "mem_get_info_free_bytes": None,
        "mem_get_info_total_bytes": None,
        "device_name": "",
    }
    if torch.cuda.is_available():
        free_bytes, total_bytes = torch.cuda.mem_get_info()
        metrics.update(
            {
                "peak_gpu_memory_reserved": int(torch.cuda.max_memory_reserved()),
                "max_gpu_memory_allocated": int(torch.cuda.max_memory_allocated()),
                "mem_get_info_free_bytes": int(free_bytes),
                "mem_get_info_total_bytes": int(total_bytes),
                "device_name": torch.cuda.get_device_name(0),
            }
        )
    return metrics


def save_audio_from_frames(
    processor: Any,
    torchaudio: Any,
    torch: Any,
    audio_frames: list[Any],
    output_path: Path,
) -> dict[str, Any]:
    if not audio_frames:
        raise RuntimeError("Liquid generation produced no audio frames.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    codes = torch.stack(audio_frames, dim=1).unsqueeze(0)
    waveform = processor.decode(codes).detach().cpu()
    if waveform.dim() == 3:
        waveform = waveform.squeeze(0)
    if waveform.dim() == 1:
        waveform = waveform.unsqueeze(0)
    save_wav_pcm16(output_path, waveform, SAMPLE_RATE, torch)
    return audio_metadata(output_path, torchaudio, torch)


def build_tts_chat(ChatState: Any, processor: Any, text: str) -> Any:
    chat = ChatState(processor)
    chat.new_turn("system")
    chat.add_text(
        "You are an offline text-to-speech engine in a synthetic feasibility test. "
        "Speak the user's text clearly. Do not add facts or sales content."
    )
    chat.end_turn()
    chat.new_turn("user")
    chat.add_text(text)
    chat.end_turn()
    chat.new_turn("assistant")
    return chat


def build_asr_chat(ChatState: Any, processor: Any, waveform: Any, sample_rate: int) -> Any:
    chat = ChatState(processor)
    chat.new_turn("system")
    chat.add_text(
        "You are an offline speech recognition engine in a synthetic feasibility test. "
        "Transcribe the user's audio exactly. Respond with transcript text only."
    )
    chat.end_turn()
    chat.new_turn("user")
    chat.add_audio(waveform, sample_rate)
    chat.end_turn()
    chat.new_turn("assistant")
    return chat


def run_tts_case(resources: dict[str, Any], case_id: str, text: str, output_path: Path) -> dict[str, Any]:
    torch = resources["torch"]
    torchaudio = resources["torchaudio"]
    processor = resources["processor"]
    model = resources["model"]
    ChatState = resources["ChatState"]
    result: dict[str, Any] = {
        "case_id": case_id,
        "input_text": text,
        "mode": "tts",
        "generation_attempted": True,
        "generation_succeeded": False,
        "exact_blocker": "",
        "output_audio_path": rel(output_path),
        "audio_committed": False,
        "duration_seconds": None,
        "sample_rate": None,
        "waveform_hash": "",
        "generation_latency_seconds": None,
        "first_audio_latency_seconds": None,
        "real_time_factor": None,
        "peak_gpu_memory_reserved": None,
        "warnings": [],
        "errors": [],
    }
    if not path_is_under(output_path, ROOT / "local_artifacts" / "audio_outputs" / "liquid"):
        result["exact_blocker"] = "Output path is outside local_artifacts/audio_outputs/liquid."
        return result

    start = time.perf_counter()
    first_audio_at: float | None = None
    tokens: list[Any] = []
    try:
        chat = build_tts_chat(ChatState, processor, text)
        for token in model.generate_interleaved(
            **chat,
            max_new_tokens=MAX_TTS_TOKENS,
            text_temperature=None,
            text_top_k=None,
            audio_temperature=None,
            audio_top_k=None,
        ):
            tokens.append(token)
            if first_audio_at is None:
                _, audio_frames = split_generated_tokens([token])
                if audio_frames:
                    first_audio_at = time.perf_counter()
        _, audio_frames = split_generated_tokens(tokens)
        metadata = save_audio_from_frames(processor, torchaudio, torch, audio_frames, output_path)
        latency = time.perf_counter() - start
        result.update(metadata)
        result["generation_latency_seconds"] = round(latency, 6)
        if first_audio_at is not None:
            result["first_audio_latency_seconds"] = round(first_audio_at - start, 6)
        duration = result.get("duration_seconds")
        if isinstance(duration, (int, float)) and duration > 0:
            result["real_time_factor"] = round(latency / float(duration), 6)
        result["generation_succeeded"] = True
        result["peak_gpu_memory_reserved"] = int(torch.cuda.max_memory_reserved()) if torch.cuda.is_available() else None
    except RuntimeError as exc:
        result["exact_blocker"] = f"{type(exc).__name__}: {exc}"
        result["errors"].append(result["exact_blocker"])
        if "out of memory" in str(exc).lower() and torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception as exc:  # pragma: no cover - evidence path
        result["exact_blocker"] = f"{type(exc).__name__}: {exc}"
        result["errors"].append(result["exact_blocker"])
        result["traceback_tail"] = traceback.format_exc().splitlines()[-8:]
    return result


def run_asr_case(
    resources: dict[str, Any],
    case_id: str,
    target_phrase: str,
    audio_path: Path,
    audio_source_type: str,
) -> dict[str, Any]:
    torch = resources["torch"]
    torchaudio = resources["torchaudio"]
    processor = resources["processor"]
    model = resources["model"]
    ChatState = resources["ChatState"]
    result: dict[str, Any] = {
        "case_id": case_id,
        "target_phrase": target_phrase,
        "audio_source_type": audio_source_type,
        "audio_input_path": rel(audio_path),
        "asr_attempted": True,
        "asr_succeeded": False,
        "transcript": "",
        "normalized_transcript": "",
        "exact_match": False,
        "fuzzy_match_score": 0.0,
        "critical_term_preserved": {},
        "latency_seconds": None,
        "exact_blocker": "",
    }
    try:
        waveform, sample_rate = load_wav_tensor(audio_path, torch)
        chat = build_asr_chat(ChatState, processor, waveform, int(sample_rate))
        tokens: list[Any] = []
        start = time.perf_counter()
        for token in model.generate_sequential(
            **chat,
            max_new_tokens=MAX_ASR_TOKENS,
            text_temperature=None,
            text_top_k=None,
            audio_temperature=None,
            audio_top_k=None,
        ):
            tokens.append(token)
        latency = time.perf_counter() - start
        text_tokens, _ = split_generated_tokens(tokens)
        transcript = decode_text_tokens(processor, text_tokens)
        normalized = normalize_text(transcript)
        exact = normalized == normalize_text(target_phrase)
        score = fuzzy_score(target_phrase, transcript)
        critical = critical_term_metrics(target_phrase, transcript)
        critical_total = int(critical.get("critical_terms_total") or 0)
        critical_preserved = int(critical.get("critical_terms_preserved_count") or 0)
        reliable = bool(transcript) and (
            exact
            or score >= 0.85
            or (critical_total > 0 and critical_preserved == critical_total)
        )
        result.update(
            {
                "asr_succeeded": reliable,
                "transcript": transcript,
                "normalized_transcript": normalized,
                "exact_match": exact,
                "fuzzy_match_score": score,
                "latency_seconds": round(latency, 6),
            }
        )
        result.update(critical)
        if not transcript:
            result["exact_blocker"] = "Liquid ASR generation returned no decodable transcript text."
        elif not reliable:
            result["exact_blocker"] = "Liquid ASR returned text, but it did not match the target phrase or preserve required critical terms."
    except RuntimeError as exc:
        result["exact_blocker"] = f"{type(exc).__name__}: {exc}"
        if "out of memory" in str(exc).lower() and torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception as exc:  # pragma: no cover - evidence path
        result["exact_blocker"] = f"{type(exc).__name__}: {exc}"
        result["traceback_tail"] = traceback.format_exc().splitlines()[-8:]
    return result


def summarize_numbers(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "min": None, "p50": None, "p90": None, "max": None, "average": None}
    ordered = sorted(values)

    def pick(percentile: float) -> float:
        index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * percentile))))
        return round(ordered[index], 6)

    return {
        "count": len(ordered),
        "min": round(ordered[0], 6),
        "p50": pick(0.5),
        "p90": pick(0.9),
        "max": round(ordered[-1], 6),
        "average": round(sum(ordered) / len(ordered), 6),
    }


def summarize_tts(cases: list[dict[str, Any]]) -> dict[str, Any]:
    succeeded = [case for case in cases if case.get("generation_succeeded") is True]
    return {
        "tts_attempted_count": sum(1 for case in cases if case.get("generation_attempted") is True),
        "tts_succeeded_count": len(succeeded),
        "latency_seconds": summarize_numbers(
            [float(case["generation_latency_seconds"]) for case in succeeded if isinstance(case.get("generation_latency_seconds"), (int, float))]
        ),
        "first_audio_latency_seconds": summarize_numbers(
            [float(case["first_audio_latency_seconds"]) for case in succeeded if isinstance(case.get("first_audio_latency_seconds"), (int, float))]
        ),
        "real_time_factor": summarize_numbers(
            [float(case["real_time_factor"]) for case in succeeded if isinstance(case.get("real_time_factor"), (int, float))]
        ),
    }


def summarize_asr(cases: list[dict[str, Any]]) -> dict[str, Any]:
    attempted = [case for case in cases if case.get("asr_attempted") is True]
    succeeded = [case for case in attempted if case.get("asr_succeeded") is True]
    total_terms = 0
    preserved_terms = 0
    for case in attempted:
        total_terms += int(case.get("critical_terms_total") or 0)
        preserved_terms += int(case.get("critical_terms_preserved_count") or 0)
    return {
        "asr_attempted_count": len(attempted),
        "asr_succeeded_count": len(succeeded),
        "audio_source_types": sorted({str(case.get("audio_source_type") or "unknown") for case in cases}),
        "exact_match_count": sum(1 for case in succeeded if case.get("exact_match") is True),
        "critical_terms_preserved_count": preserved_terms,
        "critical_terms_total": total_terms,
        "critical_term_preservation_rate": round(preserved_terms / total_terms, 6) if total_terms else None,
        "latency_seconds": summarize_numbers(
            [float(case["latency_seconds"]) for case in succeeded if isinstance(case.get("latency_seconds"), (int, float))]
        ),
    }


def model_context(config: dict[str, Any]) -> dict[str, Any]:
    model_path = ROOT / str(config.get("local_model_path") or "")
    files = model_files(model_path)
    return {
        "model_id": config.get("model_id"),
        "model_path": rel(model_path) if model_path.exists() else str(config.get("local_model_path") or ""),
        "model_present": bool(files),
        "model_files_sample": files,
    }


def write_tts_evidence(
    config: dict[str, Any],
    cases: list[dict[str, Any]],
    resources: dict[str, Any] | None,
    status: str = "pass",
    blocker: str = "",
) -> dict[str, Any]:
    succeeded_count = sum(1 for case in cases if case.get("generation_succeeded") is True)
    result = {
        "experiment_id": "LIQUID-AUDIO-SYNTHETIC-TTS-SMOKE-001",
        "generated_at": utc_now(),
        "status": status,
        "blocker": blocker,
        "config": rel(CONFIG_PATH),
        "mode": "tts_only",
        **model_context(config),
        "cases": cases,
        **summarize_tts(cases),
        "audio_files_generated": succeeded_count > 0,
        "audio_files_committed": bool(tracked_audio_files()),
        "model_weights_committed": bool(tracked_model_files()),
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "elevenlabs_calls_made": False,
        "live_tts_calls_made": False,
        "raw_private_audio_used": False,
        "raw_private_transcripts_included": False,
        "live_wiring_allowed": False,
        "sales_brain_replacement_allowed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "gpu_memory": gpu_metrics(resources["torch"]) if resources else {},
        "side_effects": side_effects(
            allowed_local_audio_generation=succeeded_count > 0,
            audio_files_generated=succeeded_count > 0,
        ),
    }
    write_json(TTS_RESULT_PATH, result)
    write_text(
        TTS_REPORT_PATH,
        "\n".join(
            [
                "# LIQUID-AUDIO-SYNTHETIC-TTS-SMOKE-001",
                "",
                f"- status: {result['status']}",
                f"- blocker: {blocker or 'none'}",
                f"- tts_attempted_count: {result['tts_attempted_count']}",
                f"- tts_succeeded_count: {result['tts_succeeded_count']}",
                f"- audio_files_generated: {str(result['audio_files_generated']).lower()}",
                f"- audio_files_committed: {str(result['audio_files_committed']).lower()}",
                f"- model_weights_committed: {str(result['model_weights_committed']).lower()}",
                f"- provider_calls_made: false",
                f"- live_wiring_allowed: false",
                f"- sales_brain_replacement_allowed: false",
                "",
                "## Latency",
                "",
                json.dumps(result["latency_seconds"], indent=2),
                "",
                "## Real-Time Factor",
                "",
                json.dumps(result["real_time_factor"], indent=2),
                "",
                "Audio files are local experiment artifacts only under `local_artifacts/audio_outputs/liquid` and are not copied into public evidence.",
            ]
        ),
    )
    return result


def write_asr_evidence(
    config: dict[str, Any],
    cases: list[dict[str, Any]],
    roundtrip_cases: list[dict[str, Any]],
    resources: dict[str, Any] | None,
    status: str = "pass",
    blocker: str = "",
) -> dict[str, Any]:
    all_cases = cases + roundtrip_cases
    audio_source_types = sorted({str(case.get("audio_source_type") or "unavailable") for case in all_cases}) if all_cases else ["unavailable"]
    loopback_only = bool(all_cases) and set(audio_source_types) == {"liquid_tts_loopback"}
    summary = summarize_asr(all_cases)
    result = {
        "experiment_id": "LIQUID-AUDIO-SYNTHETIC-ASR-SMOKE-001",
        "generated_at": utc_now(),
        "status": status,
        "blocker": blocker,
        "config": rel(CONFIG_PATH),
        **model_context(config),
        "asr_source_type": "liquid_tts_loopback" if loopback_only else ("mixed" if len(audio_source_types) > 1 else audio_source_types[0]),
        "loopback_only": loopback_only,
        "asr_quality_claim": "unproven_loopback_only" if loopback_only else "not_run_or_unproven",
        "cases": cases,
        "roundtrip_cases": roundtrip_cases,
        **summary,
        "audio_files_generated": any(case.get("audio_source_type") == "liquid_tts_loopback" for case in all_cases),
        "audio_files_committed": bool(tracked_audio_files()),
        "model_weights_committed": bool(tracked_model_files()),
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "elevenlabs_calls_made": False,
        "live_tts_calls_made": False,
        "raw_private_audio_used": False,
        "raw_private_transcripts_included": False,
        "live_wiring_allowed": False,
        "sales_brain_replacement_allowed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "gpu_memory": gpu_metrics(resources["torch"]) if resources else {},
        "side_effects": side_effects(
            allowed_local_audio_generation=any(case.get("audio_source_type") == "liquid_tts_loopback" for case in all_cases),
            audio_files_generated=any(case.get("audio_source_type") == "liquid_tts_loopback" for case in all_cases),
        ),
    }
    write_json(ASR_RESULT_PATH, result)
    write_text(
        ASR_REPORT_PATH,
        "\n".join(
            [
                "# LIQUID-AUDIO-SYNTHETIC-ASR-SMOKE-001",
                "",
                f"- status: {result['status']}",
                f"- blocker: {blocker or 'none'}",
                f"- asr_attempted_count: {result['asr_attempted_count']}",
                f"- asr_succeeded_count: {result['asr_succeeded_count']}",
                f"- asr_source_type: {result['asr_source_type']}",
                f"- loopback_only: {str(result['loopback_only']).lower()}",
                f"- critical_terms_preserved_count: {result['critical_terms_preserved_count']}",
                f"- critical_terms_total: {result['critical_terms_total']}",
                f"- provider_calls_made: false",
                f"- live_wiring_allowed: false",
                f"- sales_brain_replacement_allowed: false",
                "",
                "This is not a final ASR quality test. Loopback ASR only verifies whether Liquid can generate and consume local audio; independent ASR quality remains unproven.",
                "",
                "## Latency",
                "",
                json.dumps(result["latency_seconds"], indent=2),
            ]
        ),
    )
    return result


def write_not_run_evidence(config: dict[str, Any], status: str, blocker: str) -> None:
    empty_tts = write_tts_evidence(config, [], None, status=status, blocker=blocker)
    empty_asr = write_asr_evidence(config, [], [], None, status=status, blocker=blocker)
    write_smoke_evidence(config, empty_tts, empty_asr, status=status, blocker=blocker)
    write_smoke_decision(config, empty_tts, empty_asr, status=status, blocker=blocker)


def load_existing_evidence() -> tuple[dict[str, Any], dict[str, Any]]:
    return read_json(TTS_RESULT_PATH), read_json(ASR_RESULT_PATH)


def write_smoke_evidence(
    config: dict[str, Any],
    tts_result: dict[str, Any],
    asr_result: dict[str, Any],
    *,
    status: str = "pass",
    blocker: str = "",
) -> dict[str, Any]:
    tts_cases = tts_result.get("cases") if isinstance(tts_result.get("cases"), list) else []
    asr_cases = asr_result.get("cases") if isinstance(asr_result.get("cases"), list) else []
    roundtrip_cases = asr_result.get("roundtrip_cases") if isinstance(asr_result.get("roundtrip_cases"), list) else []
    audio_generated = bool(tts_result.get("audio_files_generated") or asr_result.get("audio_files_generated"))
    result = {
        "experiment_id": "LIQUID-AUDIO-FEASIBILITY-SMOKE-001",
        "generated_at": utc_now(),
        "status": status,
        "blocker": blocker,
        "config": rel(CONFIG_PATH),
        "env_config": rel(ENV_CONFIG_PATH) if ENV_CONFIG_PATH.is_file() else "",
        "model_config": rel(MODEL_CONFIG_PATH) if MODEL_CONFIG_PATH.is_file() else "",
        "active_python_env": sys.executable,
        "env_gates": gate_report(),
        **model_context(config),
        "model_download_attempted": False,
        "smoke_run": status == "pass",
        "modes_completed": [
            mode
            for mode, count in (
                ("tts_only", len(tts_cases)),
                ("asr_only", len(asr_cases)),
                ("roundtrip", len(roundtrip_cases)),
            )
            if count
        ],
        "asr_smoke": {
            "status": asr_result.get("status") or "not_run",
            "synthetic_phrases": ASR_PHRASES,
            "raw_private_audio_used": False,
            "source_type": asr_result.get("asr_source_type") or "unavailable",
            "summary": summarize_asr(asr_cases),
            "cases": asr_cases,
        },
        "tts_smoke": {
            "status": tts_result.get("status") or "not_run",
            "synthetic_utterances": TTS_UTTERANCES,
            "audio_files_generated": bool(tts_result.get("audio_files_generated")),
            "summary": summarize_tts(tts_cases),
            "cases": tts_cases,
        },
        "roundtrip_smoke": {
            "status": "pass" if roundtrip_cases else "not_run",
            "synthetic_phrases": ROUNDTRIP_PHRASES,
            "summary": summarize_asr(roundtrip_cases),
            "cases": roundtrip_cases,
            "quality_claim": "not_final_asr_quality_test",
        },
        "interleaved_s2s_smoke": {
            "status": "not_run",
            "reason": "This phase only used TTS and optional loopback ASR/roundtrip; live speech-to-speech remains deferred.",
        },
        "audio_files_generated": audio_generated,
        "audio_files_committed": bool(tracked_audio_files()),
        "model_weights_committed": bool(tracked_model_files()),
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "elevenlabs_calls_made": False,
        "live_tts_calls_made": False,
        "live_wiring_allowed": False,
        "sales_brain_replacement_allowed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "side_effects": side_effects(allowed_local_audio_generation=audio_generated, audio_files_generated=audio_generated),
    }
    write_json(SMOKE_RESULT_PATH, result)
    write_text(
        SMOKE_REPORT_PATH,
        "\n".join(
            [
                "# LIQUID-AUDIO-FEASIBILITY-SMOKE-001",
                "",
                f"- status: {result['status']}",
                f"- blocker: {blocker or 'none'}",
                f"- model_present: {str(result['model_present']).lower()}",
                f"- model_download_attempted: false",
                f"- smoke_run: {str(result['smoke_run']).lower()}",
                f"- tts_attempted_count: {result['tts_smoke']['summary']['tts_attempted_count']}",
                f"- tts_succeeded_count: {result['tts_smoke']['summary']['tts_succeeded_count']}",
                f"- asr_attempted_count: {result['asr_smoke']['summary']['asr_attempted_count']}",
                f"- asr_succeeded_count: {result['asr_smoke']['summary']['asr_succeeded_count']}",
                f"- roundtrip_attempted_count: {result['roundtrip_smoke']['summary']['asr_attempted_count']}",
                f"- roundtrip_succeeded_count: {result['roundtrip_smoke']['summary']['asr_succeeded_count']}",
                f"- audio_files_generated: {str(result['audio_files_generated']).lower()}",
                f"- audio_files_committed: {str(result['audio_files_committed']).lower()}",
                f"- provider_calls_made: false",
                f"- live_wiring_allowed: false",
                f"- sales_brain_replacement_allowed: false",
                "",
                "Generated audio is only an ignored local artifact under `local_artifacts/audio_outputs/liquid`; public evidence records metadata and hashes, not audio bytes.",
            ]
        ),
    )
    write_legacy_decision(result)
    return result


def write_legacy_decision(smoke: dict[str, Any]) -> None:
    environment = read_json(ENV_RESULT_PATH)
    setup = read_json(SETUP_RESULT_PATH)
    model_load = read_json(MODEL_LOAD_RESULT_PATH)
    dependency_status = environment.get("dependency_status") if isinstance(environment.get("dependency_status"), dict) else {}
    model_status = environment.get("model_status") if isinstance(environment.get("model_status"), dict) else {}
    hardware = environment.get("hardware") if isinstance(environment.get("hardware"), dict) else {}
    torch_info = hardware.get("torch") if isinstance(hardware.get("torch"), dict) else {}
    environment_status = str(environment.get("status") or "not_available")
    model_present = bool(model_status.get("model_present") or smoke.get("model_present"))
    model_load_succeeded = bool(model_load.get("load_succeeded"))
    environment_ready = environment_status in {
        "environment_ready_no_model",
        "ready_for_download_phase",
        "model_present_ready_for_load",
        "model_loaded_ready_for_smoke",
    } and not dependency_status.get("missing_required")

    if smoke.get("status") == "pass":
        recommendation_id = "synthetic_smoke_completed"
        actual_smoke_recommended = False
        next_phase = "Use the Liquid synthetic smoke evidence to decide whether to run listening review, Kokoro/ElevenLabs latency comparison, and an independent ASR benchmark. Keep Liquid out of live runtime."
    elif environment_ready and model_present and model_load_succeeded:
        recommendation_id = "synthetic_asr_tts_smoke_next"
        actual_smoke_recommended = True
        next_phase = "Run the gated ASR/TTS smoke with synthetic inputs only; keep Liquid out of live runtime and out of sales-brain decisions."
    else:
        recommendation_id = "blocked_or_architecture_only"
        actual_smoke_recommended = False
        next_phase = "Keep Liquid as architecture inspiration until blockers are resolved."

    decision = {
        "experiment_id": "LIQUID-AUDIO-FEASIBILITY-DECISION-001",
        "generated_at": utc_now(),
        "status": "pass",
        "environment_probe_result": rel(ENV_RESULT_PATH) if ENV_RESULT_PATH.is_file() else "",
        "env_setup_result": rel(SETUP_RESULT_PATH) if SETUP_RESULT_PATH.is_file() else "",
        "env_setup_status": setup.get("status", "not_available"),
        "install_success": setup.get("install_success"),
        "exact_blocker": str(setup.get("exact_blocker") or "").strip(),
        "model_load_result": rel(MODEL_LOAD_RESULT_PATH) if MODEL_LOAD_RESULT_PATH.is_file() else "",
        "model_load_succeeded": model_load_succeeded,
        "smoke_result": rel(SMOKE_RESULT_PATH),
        "environment_status": environment_status,
        "environment_ready": environment_ready,
        "dependency_status": dependency_status,
        "hardware_status": {
            "cuda_available": bool(torch_info.get("cuda_available")),
            "assessment": "cuda_available" if torch_info.get("cuda_available") else "cuda_unavailable_or_unknown_no_source_vram_requirement",
            "explicit_vram_requirement_from_source": "unknown",
        },
        "model_present": model_present,
        "download_phase_recommended": False,
        "actual_smoke_recommended": actual_smoke_recommended,
        "smoke_status": smoke.get("status"),
        "live_wiring_allowed": False,
        "sales_brain_replacement_allowed": False,
        "next_phase_recommendation": next_phase,
        "recommendation_id": recommendation_id,
        "side_effects": side_effects(
            allowed_local_audio_generation=bool(smoke.get("audio_files_generated")),
            audio_files_generated=bool(smoke.get("audio_files_generated")),
        ),
    }
    write_json(LEGACY_DECISION_RESULT_PATH, decision)
    write_text(
        LEGACY_DECISION_REPORT_PATH,
        "\n".join(
            [
                "# LIQUID-AUDIO-FEASIBILITY-DECISION-001",
                "",
                f"- status: {decision['status']}",
                f"- environment_status: {decision['environment_status']}",
                f"- model_present: {str(decision['model_present']).lower()}",
                f"- actual_smoke_recommended: {str(decision['actual_smoke_recommended']).lower()}",
                f"- smoke_status: {decision['smoke_status']}",
                f"- live_wiring_allowed: false",
                f"- sales_brain_replacement_allowed: false",
                f"- recommendation_id: `{decision['recommendation_id']}`",
                "",
                "## Recommendation",
                "",
                str(decision["next_phase_recommendation"]),
            ]
        ),
    )


def write_smoke_decision(
    config: dict[str, Any],
    tts_result: dict[str, Any],
    asr_result: dict[str, Any],
    *,
    status: str = "pass",
    blocker: str = "",
) -> dict[str, Any]:
    tts_summary = {
        "attempted": int(tts_result.get("tts_attempted_count") or 0),
        "succeeded": int(tts_result.get("tts_succeeded_count") or 0),
        "latency_seconds": tts_result.get("latency_seconds") or {},
        "real_time_factor": tts_result.get("real_time_factor") or {},
    }
    asr_summary = {
        "attempted": int(asr_result.get("asr_attempted_count") or 0),
        "succeeded": int(asr_result.get("asr_succeeded_count") or 0),
        "source_type": asr_result.get("asr_source_type") or "unavailable",
        "loopback_only": bool(asr_result.get("loopback_only")),
        "critical_terms_preserved_count": int(asr_result.get("critical_terms_preserved_count") or 0),
        "critical_terms_total": int(asr_result.get("critical_terms_total") or 0),
        "critical_term_preservation_rate": asr_result.get("critical_term_preservation_rate"),
    }
    tts_rtf = (tts_result.get("real_time_factor") or {}).get("average") if isinstance(tts_result.get("real_time_factor"), dict) else None
    tts_latency = (tts_result.get("latency_seconds") or {}).get("p50") if isinstance(tts_result.get("latency_seconds"), dict) else None

    if status != "pass":
        recommendation_id = "smoke_not_run_or_blocked"
        recommendation = "Resolve the recorded blocker before further Liquid audio testing."
    elif tts_summary["succeeded"] and isinstance(tts_rtf, (int, float)) and tts_rtf <= 1.5:
        recommendation_id = "listening_review_and_latency_comparison_next"
        recommendation = "TTS generated local audio with reasonable RTF. Run listening review and compare Liquid against Kokoro and ElevenLabs latency/quality before any product decision."
    elif tts_summary["succeeded"]:
        recommendation_id = "offline_candidate_or_architecture_inspiration"
        recommendation = "TTS generated local audio but latency/RTF is not yet strong enough for live use. Keep Liquid as offline candidate or architecture inspiration pending comparison."
    else:
        recommendation_id = "liquid_generation_blocked"
        recommendation = "Liquid did not produce usable TTS audio in this smoke. Fix the blocker or keep it as architecture inspiration."

    if asr_summary["loopback_only"] and asr_summary["succeeded"]:
        asr_recommendation = "ASR only succeeded in loopback; independent ASR quality is unproven and needs a separate synthetic or recorded benchmark."
    elif asr_summary["loopback_only"]:
        asr_recommendation = "Loopback ASR did not preserve critical terms; independent ASR quality is unproven and needs a separate synthetic or recorded benchmark after prompt/runtime blockers are understood."
    elif asr_summary["succeeded"]:
        asr_recommendation = "ASR produced transcripts; run an independent ASR benchmark on controlled synthetic/recorded inputs next."
    else:
        asr_recommendation = "ASR remains unproven."

    decision = {
        "experiment_id": "LIQUID-AUDIO-SMOKE-DECISION-001",
        "generated_at": utc_now(),
        "status": "pass" if status == "pass" else status,
        "blocker": blocker,
        "config": rel(CONFIG_PATH),
        **model_context(config),
        "tts_summary": tts_summary,
        "asr_summary": asr_summary,
        "recommendation_id": recommendation_id,
        "next_phase_recommendation": recommendation,
        "asr_next_phase_recommendation": asr_recommendation,
        "latency_assessment": {
            "tts_average_rtf": tts_rtf,
            "tts_p50_generation_latency_seconds": tts_latency,
            "reasonable_rtf_threshold": 1.5,
        },
        "live_wiring_allowed": False,
        "sales_brain_replacement_allowed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "elevenlabs_calls_made": False,
        "live_tts_calls_made": False,
        "raw_private_audio_used": False,
        "raw_private_transcripts_included": False,
        "side_effects": side_effects(
            allowed_local_audio_generation=bool(tts_result.get("audio_files_generated") or asr_result.get("audio_files_generated")),
            audio_files_generated=bool(tts_result.get("audio_files_generated") or asr_result.get("audio_files_generated")),
        ),
    }
    write_json(DECISION_RESULT_PATH, decision)
    write_text(
        DECISION_REPORT_PATH,
        "\n".join(
            [
                "# LIQUID-AUDIO-SMOKE-DECISION-001",
                "",
                f"- status: {decision['status']}",
                f"- blocker: {blocker or 'none'}",
                f"- recommendation_id: `{recommendation_id}`",
                f"- tts_attempted: {tts_summary['attempted']}",
                f"- tts_succeeded: {tts_summary['succeeded']}",
                f"- asr_attempted: {asr_summary['attempted']}",
                f"- asr_succeeded: {asr_summary['succeeded']}",
                f"- asr_source_type: {asr_summary['source_type']}",
                f"- live_wiring_allowed: false",
                f"- sales_brain_replacement_allowed: false",
                "",
                "## Recommendation",
                "",
                recommendation,
                "",
                "## ASR Caution",
                "",
                asr_recommendation,
            ]
        ),
    )
    return decision


def run_tts(resources: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    output_root = ROOT / "local_artifacts" / "audio_outputs" / "liquid" / "tts_smoke"
    for index, text in enumerate(TTS_UTTERANCES[:limit], start=1):
        case_id = f"tts_{index:02d}"
        output_path = output_root / f"{case_id}.wav"
        cases.append(run_tts_case(resources, case_id, text, output_path))
    return cases


def run_loopback_asr(resources: dict[str, Any], phrases: list[str], prefix: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    asr_cases: list[dict[str, Any]] = []
    loopback_tts_cases: list[dict[str, Any]] = []
    output_root = ROOT / "local_artifacts" / "audio_outputs" / "liquid" / f"{prefix}_loopback"
    for index, phrase in enumerate(phrases, start=1):
        case_id = f"{prefix}_{index:02d}"
        audio_path = output_root / f"{case_id}.wav"
        tts_case = run_tts_case(resources, f"{case_id}_tts_source", phrase, audio_path)
        loopback_tts_cases.append(tts_case)
        if not tts_case.get("generation_succeeded"):
            metrics = critical_term_metrics(phrase, "")
            asr_cases.append(
                {
                    "case_id": case_id,
                    "target_phrase": phrase,
                    "audio_source_type": "unavailable",
                    "audio_input_path": rel(audio_path),
                    "asr_attempted": False,
                    "asr_succeeded": False,
                    "transcript": "",
                    "normalized_transcript": "",
                    "exact_match": False,
                    "fuzzy_match_score": 0.0,
                    **metrics,
                    "latency_seconds": None,
                    "exact_blocker": f"no synthetic audio source: {tts_case.get('exact_blocker') or 'Liquid TTS loopback generation failed'}",
                }
            )
            continue
        asr_cases.append(run_asr_case(resources, case_id, phrase, audio_path, "liquid_tts_loopback"))
    return asr_cases, loopback_tts_cases


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run gated Liquid Audio synthetic ASR/TTS smoke.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--tts-only", action="store_true", help="Run only synthetic TTS smoke.")
    mode.add_argument("--asr-only", action="store_true", help="Run only loopback ASR smoke.")
    mode.add_argument("--roundtrip", action="store_true", help="Run limited loopback roundtrip smoke.")
    parser.add_argument("--limit", type=int, default=0, help="Limit cases for the selected mode.")
    parser.add_argument("--metadata-only", action="store_true", help="Write gate/model metadata without loading or generating.")
    parser.add_argument("--skip-if-missing-model", action="store_true", help="Exit 0 with model_missing evidence when files are absent.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = read_json(CONFIG_PATH)
    if not config:
        raise AssertionError(f"Missing config: {rel(CONFIG_PATH)}")

    model_path = ROOT / str(config.get("local_model_path") or "")
    files = model_files(model_path)
    if not gates_enabled():
        blocker = "ENABLE_LOCAL_AUDIO_EXPERIMENT=1, LOCAL_LIQUID_AUDIO_ENABLED=true, LOCAL_LIQUID_ALLOW_MODEL_LOAD=1, and LOCAL_LIQUID_ALLOW_INFERENCE=1 are required."
        write_not_run_evidence(config, "not_run", blocker)
        print(json.dumps({"status": "not_run", "blocker": blocker, "model_present": bool(files)}, indent=2))
        return 0
    if not files:
        blocker = "Model files are missing; this smoke does not download weights."
        write_not_run_evidence(config, "model_missing", blocker)
        print(json.dumps({"status": "model_missing", "blocker": blocker, "model_present": False}, indent=2))
        return 0
    if args.metadata_only:
        blocker = "metadata-only mode requested; no model load or inference attempted."
        write_not_run_evidence(config, "not_run", blocker)
        print(json.dumps({"status": "not_run", "blocker": blocker, "model_present": True}, indent=2))
        return 0

    resources: dict[str, Any] = {}
    try:
        resources = load_liquid(model_path)
        tts_result, asr_result = load_existing_evidence()
        if args.tts_only:
            limit = args.limit or len(TTS_UTTERANCES)
            tts_cases = run_tts(resources, min(limit, len(TTS_UTTERANCES)))
            tts_result = write_tts_evidence(config, tts_cases, resources)
        elif args.asr_only:
            limit = args.limit or len(ASR_PHRASES)
            asr_cases, _ = run_loopback_asr(resources, ASR_PHRASES[: min(limit, len(ASR_PHRASES))], "asr")
            existing_roundtrip = asr_result.get("roundtrip_cases") if isinstance(asr_result.get("roundtrip_cases"), list) else []
            asr_result = write_asr_evidence(config, asr_cases, existing_roundtrip, resources)
        elif args.roundtrip:
            limit = args.limit or len(ROUNDTRIP_PHRASES)
            roundtrip_cases, _ = run_loopback_asr(resources, ROUNDTRIP_PHRASES[: min(limit, len(ROUNDTRIP_PHRASES))], "roundtrip")
            existing_cases = asr_result.get("cases") if isinstance(asr_result.get("cases"), list) else []
            asr_result = write_asr_evidence(config, existing_cases, roundtrip_cases, resources)
        else:
            tts_cases = run_tts(resources, len(TTS_UTTERANCES))
            tts_result = write_tts_evidence(config, tts_cases, resources)
            asr_cases, _ = run_loopback_asr(resources, ASR_PHRASES, "asr")
            roundtrip_cases, _ = run_loopback_asr(resources, ROUNDTRIP_PHRASES, "roundtrip")
            asr_result = write_asr_evidence(config, asr_cases, roundtrip_cases, resources)

        if not tts_result:
            tts_result = write_tts_evidence(config, [], resources, status="not_run", blocker="TTS mode has not been run yet.")
        if not asr_result:
            asr_result = write_asr_evidence(config, [], [], resources, status="not_run", blocker="ASR mode has not been run yet.")

        smoke = write_smoke_evidence(config, tts_result, asr_result)
        decision = write_smoke_decision(config, tts_result, asr_result)
        print(
            json.dumps(
                {
                    "status": smoke.get("status"),
                    "mode": "tts_only" if args.tts_only else "asr_only" if args.asr_only else "roundtrip" if args.roundtrip else "all",
                    "tts_succeeded": (tts_result or {}).get("tts_succeeded_count"),
                    "asr_succeeded": (asr_result or {}).get("asr_succeeded_count"),
                    "recommendation_id": decision.get("recommendation_id"),
                    "audio_files_generated": smoke.get("audio_files_generated"),
                    "model_present": True,
                },
                indent=2,
            )
        )
        return 0
    except RuntimeError as exc:
        blocker = f"{type(exc).__name__}: {exc}"
        if "out of memory" in str(exc).lower() and resources.get("torch") is not None and resources["torch"].cuda.is_available():
            resources["torch"].cuda.empty_cache()
        write_not_run_evidence(config, "blocked", blocker)
        print(json.dumps({"status": "blocked", "blocker": blocker, "model_present": True}, indent=2))
        return 0
    except Exception as exc:  # pragma: no cover - evidence path
        blocker = f"{type(exc).__name__}: {exc}"
        write_not_run_evidence(config, "blocked", blocker)
        print(json.dumps({"status": "blocked", "blocker": blocker, "model_present": True}, indent=2))
        return 0
    finally:
        if resources:
            unload_liquid(resources)


if __name__ == "__main__":
    raise SystemExit(main())
