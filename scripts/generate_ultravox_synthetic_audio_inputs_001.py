#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import wave
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "local_artifacts" / "audio_outputs" / "ultravox" / "synthetic_inputs"
EVIDENCE_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-SYNTHETIC-AUDIO-INPUTS-001"
RESULT_PATH = EVIDENCE_DIR / "result.json"
REPORT_PATH = EVIDENCE_DIR / "report.md"
SYNTHETIC_TEXTS = ["What is this?", "Don't put me in CRM."]
TARGET_SAMPLE_RATE = 48000
TARGET_CHANNELS = 1
TARGET_SAMPLE_WIDTH = 2


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def wav_metadata(path: Path) -> dict[str, Any]:
    with wave.open(str(path), "rb") as wav_file:
        frames = wav_file.getnframes()
        sample_rate = wav_file.getframerate()
        return {
            "sample_rate": sample_rate,
            "channels": wav_file.getnchannels(),
            "sample_width_bytes": wav_file.getsampwidth(),
            "frame_count": frames,
            "duration_seconds": round(frames / float(sample_rate), 3) if sample_rate else 0.0,
        }


def quote_powershell(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def powershell_executable() -> str | None:
    for name in ("powershell.exe", "powershell", "pwsh.exe", "pwsh"):
        found = shutil.which(name)
        if found:
            return found
    return None


def generate_with_system_speech(text: str, output_path: Path) -> tuple[bool, str | None]:
    executable = powershell_executable()
    if not executable:
        return False, "PowerShell executable was not found for local System.Speech generation."
    output_path.parent.mkdir(parents=True, exist_ok=True)
    script = "\n".join(
        [
            "$ErrorActionPreference = 'Stop'",
            "Add-Type -AssemblyName System.Speech",
            "$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer",
            "$format = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(48000, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono)",
            f"$synth.SetOutputToWaveFile({quote_powershell(str(output_path))}, $format)",
            f"$synth.Speak({quote_powershell(text)}) | Out-Null",
            "$synth.Dispose()",
        ]
    )
    completed = subprocess.run(
        [executable, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    if completed.returncode != 0:
        detail = " ".join((completed.stderr or completed.stdout or "").split())[:500]
        return False, detail or "System.Speech generation failed without diagnostic output."
    return True, None


def generate_with_sapi_spvoice(text: str, output_path: Path) -> tuple[bool, str | None]:
    try:
        import win32com.client  # type: ignore[import-not-found]
        from win32com.client import constants  # type: ignore[import-not-found]
    except Exception as error:
        return False, f"pywin32 SAPI COM support is unavailable: {error}"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        voice = win32com.client.gencache.EnsureDispatch("SAPI.SpVoice")
        stream = win32com.client.gencache.EnsureDispatch("SAPI.SpFileStream")
        audio_format = win32com.client.gencache.EnsureDispatch("SAPI.SpAudioFormat")
        audio_format.Type = constants.SAFT48kHz16BitMono
        stream.Format = audio_format
        stream.Open(str(output_path), constants.SSFMCreateForWrite, False)
        voice.AudioOutputStream = stream
        voice.Speak(text)
        stream.Close()
    except Exception as error:
        try:
            stream.Close()  # type: ignore[name-defined]
        except Exception:
            pass
        return False, f"SAPI.SpVoice generation failed: {error}"
    return True, None


def validate_generated_files(paths: list[Path]) -> tuple[bool, str | None, list[dict[str, Any]]]:
    metadata: list[dict[str, Any]] = []
    for path in paths:
        if not path.is_file() or path.stat().st_size <= 44:
            return False, f"Generated audio file is missing or too small: {rel(path)}", metadata
        try:
            info = wav_metadata(path)
        except wave.Error as error:
            return False, f"Generated audio is not a readable WAV file: {error}", metadata
        metadata.append(info)
        if info["sample_rate"] != TARGET_SAMPLE_RATE or info["channels"] != TARGET_CHANNELS or info["sample_width_bytes"] != TARGET_SAMPLE_WIDTH:
            return False, f"Generated WAV must be 48000 Hz 16-bit mono; got {info}", metadata
    return True, None, metadata


def base_result() -> dict[str, Any]:
    return {
        "evaluation_id": "ULTRAVOX-SYNTHETIC-AUDIO-INPUTS-001",
        "phase": "4J5",
        "generation_attempted": False,
        "generation_succeeded": False,
        "generator_used": None,
        "input_texts": SYNTHETIC_TEXTS,
        "output_paths": [],
        "sample_rate": None,
        "duration_seconds": [],
        "file_hashes": [],
        "audio_files_committed": False,
        "provider_calls_made": False,
        "blocker": None,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }


def generate_synthetic_audio_inputs() -> dict[str, Any]:
    result = base_result()
    result["generation_attempted"] = True
    paths = [OUT_DIR / f"ultravox_synthetic_user_turn_{index:02d}.wav" for index, _ in enumerate(SYNTHETIC_TEXTS, start=1)]
    result["output_paths"] = [rel(path) for path in paths]
    system_speech_errors: list[str] = []
    for text, path in zip(SYNTHETIC_TEXTS, paths):
        ok, error = generate_with_system_speech(text, path)
        if not ok:
            system_speech_errors.append(str(error))
            break
    if system_speech_errors:
        sapi_errors: list[str] = []
        for text, path in zip(SYNTHETIC_TEXTS, paths):
            ok, error = generate_with_sapi_spvoice(text, path)
            if not ok:
                sapi_errors.append(str(error))
                break
        if sapi_errors:
            result["generator_used"] = "windows_system_speech_sapi"
            result["blocker"] = "System.Speech failed; SAPI.SpVoice fallback failed. " + " ".join((system_speech_errors + sapi_errors))[:700]
            return result
        result["generator_used"] = "windows_sapi_spvoice"
    else:
        result["generator_used"] = "windows_system_speech_sapi"
    ok, error, metadata = validate_generated_files(paths)
    if not ok:
        result["blocker"] = error
        return result
    result["generation_succeeded"] = True
    result["sample_rate"] = TARGET_SAMPLE_RATE
    result["duration_seconds"] = [item["duration_seconds"] for item in metadata]
    result["file_hashes"] = [sha256_file(path) for path in paths]
    return result


def render_report(result: dict[str, Any]) -> str:
    output_lines = [f"- `{path}`" for path in result.get("output_paths", [])] or ["- None"]
    return "\n".join(
        [
            "# ULTRAVOX-SYNTHETIC-AUDIO-INPUTS-001",
            "",
            f"Generation attempted: `{str(result['generation_attempted']).lower()}`",
            f"Generation succeeded: `{str(result['generation_succeeded']).lower()}`",
            f"Generator used: `{result['generator_used']}`",
            f"Sample rate: `{result['sample_rate']}`",
            f"Duration seconds: `{result['duration_seconds']}`",
            f"File hashes recorded: `{len(result['file_hashes'])}`",
            f"Audio files committed: `{str(result['audio_files_committed']).lower()}`",
            f"Provider calls made: `{str(result['provider_calls_made']).lower()}`",
            f"Blocker: `{result['blocker']}`",
            "",
            "## Outputs",
            *output_lines,
            "",
        ]
    )


def persist_result(result: dict[str, Any]) -> None:
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, render_report(result))


def main() -> None:
    result = generate_synthetic_audio_inputs()
    persist_result(result)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
