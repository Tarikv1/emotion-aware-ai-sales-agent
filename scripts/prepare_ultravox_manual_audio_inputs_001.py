#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import wave
from array import array
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANUAL_INPUT_DIR = ROOT / "local_artifacts" / "audio_outputs" / "ultravox" / "manual_inputs"
PREPARED_INPUT_DIR = ROOT / "local_artifacts" / "audio_outputs" / "ultravox" / "prepared_inputs"
EVIDENCE_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-MANUAL-AUDIO-INPUTS-001"
RESULT_PATH = EVIDENCE_DIR / "result.json"
REPORT_PATH = EVIDENCE_DIR / "report.md"
SUPPORTED_EXTENSIONS = (".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg")
EXPECTED_CASES = [
    {"case_id": "manual_01_what_is_this", "expected_spoken_content": "What is this?"},
    {"case_id": "manual_02_dont_put_me_in_crm", "expected_spoken_content": "Don't put me in CRM."},
]
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
            "sample_width": wav_file.getsampwidth(),
            "frame_count": frames,
            "duration_seconds": round(frames / float(sample_rate), 3) if sample_rate else 0.0,
            "compression": wav_file.getcomptype(),
        }


def safe_audio_metadata(path: Path) -> dict[str, Any]:
    if path.suffix.lower() != ".wav":
        return {
            "path": rel(path),
            "extension": path.suffix.lower(),
            "file_hash": sha256_file(path),
            "metadata_available": False,
        }
    metadata = wav_metadata(path)
    return {
        "path": rel(path),
        "extension": path.suffix.lower(),
        "file_hash": sha256_file(path),
        "metadata_available": True,
        **metadata,
    }


def find_case_files() -> tuple[list[dict[str, Any]], list[str]]:
    found: list[dict[str, Any]] = []
    blockers: list[str] = []
    if not MANUAL_INPUT_DIR.is_dir():
        return found, [f"Manual input folder is missing: {rel(MANUAL_INPUT_DIR)}"]
    for case in EXPECTED_CASES:
        matches = []
        for extension in SUPPORTED_EXTENSIONS:
            candidate = MANUAL_INPUT_DIR / f"{case['case_id']}{extension}"
            if candidate.is_file():
                matches.append(candidate)
        if not matches:
            blockers.append(f"Missing manual input for {case['case_id']} with one of: {', '.join(SUPPORTED_EXTENSIONS)}")
            continue
        chosen = matches[0]
        found.append(
            {
                "case_id": case["case_id"],
                "expected_spoken_content": case["expected_spoken_content"],
                **safe_audio_metadata(chosen),
            }
        )
    return found, blockers


def ffmpeg_path() -> str | None:
    return shutil.which("ffmpeg")


def convert_with_ffmpeg(source: Path, target: Path, executable: str) -> tuple[bool, str | None]:
    target.parent.mkdir(parents=True, exist_ok=True)
    command = [
        executable,
        "-y",
        "-i",
        str(source),
        "-ac",
        "1",
        "-ar",
        str(TARGET_SAMPLE_RATE),
        "-sample_fmt",
        "s16",
        str(target),
    ]
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=60, check=False)
    if completed.returncode != 0:
        detail = " ".join((completed.stderr or completed.stdout or "").split())[:500]
        return False, detail or "ffmpeg conversion failed without diagnostic output."
    return True, None


def pcm16_samples_to_mono(raw: bytes, channels: int) -> array:
    samples = array("h")
    samples.frombytes(raw)
    if sys.byteorder != "little":
        samples.byteswap()
    if channels == 1:
        return samples
    mono = array("h")
    for offset in range(0, len(samples), channels):
        frame = samples[offset : offset + channels]
        if frame:
            mono.append(int(sum(frame) / len(frame)))
    return mono


def integer_resample(samples: array, source_rate: int) -> tuple[array, str | None]:
    if source_rate == TARGET_SAMPLE_RATE:
        return samples, None
    if source_rate > 0 and TARGET_SAMPLE_RATE % source_rate == 0:
        factor = TARGET_SAMPLE_RATE // source_rate
        output = array("h")
        for sample in samples:
            output.extend([sample] * factor)
        return output, None
    if source_rate > TARGET_SAMPLE_RATE and source_rate % TARGET_SAMPLE_RATE == 0:
        factor = source_rate // TARGET_SAMPLE_RATE
        return array("h", samples[::factor]), None
    return array("h"), f"Python WAV path only supports exact integer sample-rate conversion to {TARGET_SAMPLE_RATE} Hz; got {source_rate} Hz."


def convert_with_python_wave(source: Path, target: Path) -> tuple[bool, str | None, str | None]:
    if source.suffix.lower() != ".wav":
        return False, "Python wave fallback only supports WAV input.", None
    try:
        with wave.open(str(source), "rb") as wav_file:
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            sample_rate = wav_file.getframerate()
            compression = wav_file.getcomptype()
            frames = wav_file.readframes(wav_file.getnframes())
    except wave.Error as error:
        return False, f"Input WAV could not be read: {error}", None
    if compression != "NONE":
        return False, f"Python wave fallback requires PCM WAV; got compression {compression}.", None
    if sample_width != TARGET_SAMPLE_WIDTH:
        return False, f"Python wave fallback requires 16-bit PCM input; got sample_width {sample_width}.", None
    samples = pcm16_samples_to_mono(frames, channels)
    converted, error = integer_resample(samples, sample_rate)
    if error:
        return False, error, None
    target.parent.mkdir(parents=True, exist_ok=True)
    output = converted
    if sys.byteorder != "little":
        output = array("h", converted)
        output.byteswap()
    with wave.open(str(target), "wb") as wav_file:
        wav_file.setnchannels(TARGET_CHANNELS)
        wav_file.setsampwidth(TARGET_SAMPLE_WIDTH)
        wav_file.setframerate(TARGET_SAMPLE_RATE)
        wav_file.writeframes(output.tobytes())
    converter = "python_wave_pcm_copy" if channels == TARGET_CHANNELS and sample_rate == TARGET_SAMPLE_RATE else "python_wave_pcm_integer_resample"
    return True, None, converter


def base_result() -> dict[str, Any]:
    return {
        "evaluation_id": "ULTRAVOX-MANUAL-AUDIO-INPUTS-001",
        "phase": "4J5B",
        "status": "not_run",
        "manual_input_folder": rel(MANUAL_INPUT_DIR),
        "manual_input_folder_exists": MANUAL_INPUT_DIR.is_dir(),
        "supported_extensions": list(SUPPORTED_EXTENSIONS),
        "input_files_found": 0,
        "expected_case_count": len(EXPECTED_CASES),
        "prepared_case_count": 0,
        "conversion_attempted": False,
        "conversion_succeeded": False,
        "converter_used": None,
        "ffmpeg_available": bool(ffmpeg_path()),
        "torchaudio_available": False,
        "blockers": [],
        "input_files": [],
        "prepared_files": [],
        "duration_seconds": [],
        "sample_rate": [],
        "channels": [],
        "sample_width": [],
        "file_hash": [],
        "audio_files_committed": False,
        "provider_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }


def prepare_manual_audio_inputs() -> dict[str, Any]:
    result = base_result()
    found, blockers = find_case_files()
    result["input_files"] = found
    result["input_files_found"] = len(found)
    result["blockers"].extend(blockers)
    if blockers:
        result["status"] = "missing_manual_inputs"
        return result

    converter_used: str | None = None
    result["conversion_attempted"] = True
    executable = ffmpeg_path()
    prepared: list[dict[str, Any]] = []
    for item in found:
        source = ROOT / item["path"]
        target = PREPARED_INPUT_DIR / f"{item['case_id']}_prepared_48k_s16le_mono.wav"
        if executable:
            ok, error = convert_with_ffmpeg(source, target, executable)
            converter = "ffmpeg"
        else:
            ok, error, converter = convert_with_python_wave(source, target)
        if not ok:
            result["blockers"].append(f"{item['case_id']}: {error}")
            continue
        converter_used = converter_used or converter
        metadata = wav_metadata(target)
        prepared.append(
            {
                "case_id": item["case_id"],
                "expected_spoken_content": item["expected_spoken_content"],
                "source_path": item["path"],
                "path": rel(target),
                "converter_used": converter,
                "file_hash": sha256_file(target),
                **metadata,
            }
        )

    result["prepared_files"] = prepared
    result["prepared_case_count"] = len(prepared)
    result["converter_used"] = converter_used
    result["duration_seconds"] = [item["duration_seconds"] for item in prepared]
    result["sample_rate"] = [item["sample_rate"] for item in prepared]
    result["channels"] = [item["channels"] for item in prepared]
    result["sample_width"] = [item["sample_width"] for item in prepared]
    result["file_hash"] = [item["file_hash"] for item in prepared]
    if len(prepared) == len(EXPECTED_CASES) and not result["blockers"]:
        result["status"] = "prepared_manual_inputs"
        result["conversion_succeeded"] = True
    else:
        result["status"] = "conversion_failed"
        result["conversion_succeeded"] = False
        if not executable and not prepared:
            result["blockers"].append("ffmpeg is unavailable and Python WAV conversion could not prepare the manual inputs.")
    return result


def render_report(result: dict[str, Any]) -> str:
    prepared_lines = [f"- `{item['path']}` ({item['duration_seconds']}s, {item['sample_rate']} Hz)" for item in result.get("prepared_files", [])] or ["- None"]
    blocker_lines = [f"- {blocker}" for blocker in result.get("blockers", [])] or ["- None"]
    return "\n".join(
        [
            "# ULTRAVOX-MANUAL-AUDIO-INPUTS-001",
            "",
            f"Status: `{result['status']}`",
            f"Manual input folder exists: `{str(result['manual_input_folder_exists']).lower()}`",
            f"Input files found: `{result['input_files_found']}`",
            f"Expected case count: `{result['expected_case_count']}`",
            f"Prepared case count: `{result['prepared_case_count']}`",
            f"Conversion attempted: `{str(result['conversion_attempted']).lower()}`",
            f"Conversion succeeded: `{str(result['conversion_succeeded']).lower()}`",
            f"Converter used: `{result['converter_used']}`",
            f"ffmpeg available: `{str(result['ffmpeg_available']).lower()}`",
            f"Audio files committed: `{str(result['audio_files_committed']).lower()}`",
            f"Provider calls made: `{str(result['provider_calls_made']).lower()}`",
            "",
            "## Prepared Files",
            *prepared_lines,
            "",
            "## Blockers",
            *blocker_lines,
            "",
        ]
    )


def main() -> None:
    result = prepare_manual_audio_inputs()
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, render_report(result))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
