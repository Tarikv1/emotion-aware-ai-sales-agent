#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from private_speech_learning_queue import process_capture_record


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_DATA_ROOT = ROOT / "data" / "private"
DEFAULT_PRIVATE_ROOT = PRIVATE_DATA_ROOT / "tarik-speech-samples"
WHATSAPP_DROP_DIRNAME = "whatsapp-voice-notes"
CONVERTED_AUDIO_DIRNAME = "converted-audio"
MANIFEST_RELATIVE = Path("derived") / "local-audio-conversion-manifest.jsonl"
REPORT_RELATIVE = Path("derived") / "local-audio-conversion-report.md"
SOURCE_EXTENSION_FOCUS = ".ogg"
SUPPORTED_SOURCE_EXTENSIONS = {".ogg"}
DEFERRED_SOURCE_EXTENSIONS = {".mp3", ".m4a", ".aac", ".opus", ".flac", ".webm", ".wma", ".caf", ".amr"}
DROP_FOLDER_README = "README.txt"


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def is_under(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def project_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_stem(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip(".-_").lower()
    return cleaned[:80] or "whatsapp-voice-note"


def redact_process_text(text: str) -> str:
    redacted = text.replace(str(ROOT), "<project-root>")
    return redacted[-1000:]


def ensure_under_private(path: Path, label: str) -> None:
    if not is_under(path, PRIVATE_DATA_ROOT):
        raise ValueError(f"VOICE-032 {label} must stay under data/private/.")


def write_drop_folder_readme(drop_dir: Path) -> None:
    readme = drop_dir / DROP_FOLDER_README
    if readme.exists():
        return
    readme.write_text(
        "\n".join(
            [
                "VOICE-032 WhatsApp voice-note drop folder",
                "",
                "Put exported WhatsApp .ogg voice notes here.",
                "These files are local-only and ignored by Git because they live under data/private/.",
                "Run scripts/run_voice_032_local_audio_conversion.py to convert .ogg files to WAV locally.",
                "Do not put customer recordings here unless you have consent and a reviewed data-use reason.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def ensure_conversion_workspace(
    private_root: Path,
    *,
    input_dir: Path | None = None,
    converted_dir: Path | None = None,
) -> tuple[Path, Path, Path, Path]:
    ensure_under_private(private_root, "private root")
    source_dir = input_dir or private_root / WHATSAPP_DROP_DIRNAME
    wav_dir = converted_dir or private_root / CONVERTED_AUDIO_DIRNAME
    ensure_under_private(source_dir, "input directory")
    ensure_under_private(wav_dir, "converted output directory")
    if not is_under(source_dir, private_root):
        raise ValueError("VOICE-032 input directory must stay under the selected private root.")
    if not is_under(wav_dir, private_root):
        raise ValueError("VOICE-032 converted output directory must stay under the selected private root.")

    manifest_path = private_root / MANIFEST_RELATIVE
    report_path = private_root / REPORT_RELATIVE
    source_dir.mkdir(parents=True, exist_ok=True)
    wav_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    write_drop_folder_readme(source_dir)
    return source_dir, wav_dir, manifest_path, report_path


def converter_available(converter_command: list[str]) -> bool:
    if not converter_command:
        return False
    executable = converter_command[0]
    path = Path(executable)
    if path.is_absolute() or any(sep in executable for sep in ("/", "\\")):
        return path.exists()
    return shutil.which(executable) is not None


def discover_audio_files(input_dir: Path, *, include_unsupported: bool = False) -> list[Path]:
    extensions = SUPPORTED_SOURCE_EXTENSIONS | (DEFERRED_SOURCE_EXTENSIONS if include_unsupported else set())
    return sorted(path for path in input_dir.iterdir() if path.is_file() and path.suffix.lower() in extensions)


def allocate_converted_path(converted_dir: Path, source_path: Path) -> Path:
    stem = safe_stem(source_path.stem)
    candidate = converted_dir / f"{stem}.wav"
    if not candidate.exists():
        return candidate
    for index in range(2, 1000):
        candidate = converted_dir / f"{stem}-{index}.wav"
        if not candidate.exists():
            return candidate
    raise ValueError(f"Could not allocate converted WAV path for {source_path.name}.")


def conversion_privacy_boundary() -> dict[str, Any]:
    return {
        "outputs_stay_under_data_private": True,
        "provider_calls_made": False,
        "transcription_created": False,
        "voice_cloning_used": False,
        "runtime_profile_applied": False,
        "public_artifact_created": False,
        "human_review_required_before_runtime_use": True,
    }


def build_capture_record(
    *,
    source_path: Path,
    converted_path: Path,
    language: str,
    label: str,
) -> dict[str, Any]:
    sample_id = safe_stem(source_path.stem)
    return {
        "voice_milestone": "VOICE-032",
        "captured_at_utc": utc_now(),
        "mode": "local_audio_conversion",
        "sample_id": sample_id,
        "language": language,
        "label": label,
        "source_kind": "whatsapp_voice_note_converted",
        "stored_relative_path": project_relative(converted_path),
        "file_extension": ".wav",
        "byte_count": converted_path.stat().st_size,
        "content_sha256": sha256_file(converted_path),
        "content_type": "audio/wav",
        "source_audio": {
            "source_kind": "whatsapp_voice_note",
            "source_relative_path": project_relative(source_path),
            "source_file_extension": source_path.suffix.lower(),
            "source_content_sha256": sha256_file(source_path),
        },
        "privacy_boundary": {
            **conversion_privacy_boundary(),
            "stored_under_data_private": is_under(converted_path, PRIVATE_DATA_ROOT),
        },
    }


def build_status_record(
    *,
    source_path: Path,
    status: str,
    converted_path: Path | None = None,
    learning_queue: dict[str, Any] | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "voice_milestone": "VOICE-032",
        "processed_at_utc": utc_now(),
        "source_kind": "whatsapp_voice_note",
        "source_relative_path": project_relative(source_path),
        "source_extension": source_path.suffix.lower(),
        "source_content_sha256": sha256_file(source_path),
        "conversion_status": status,
        "converted_relative_path": project_relative(converted_path) if converted_path else None,
        "learning_queue": learning_queue,
        "privacy_boundary": conversion_privacy_boundary(),
    }
    if error:
        record["error"] = error
    return record


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def convert_source_file(
    source_path: Path,
    *,
    converted_dir: Path,
    private_root: Path,
    converter_command: list[str],
    timeout_seconds: int,
    language: str,
    label: str,
) -> dict[str, Any]:
    extension = source_path.suffix.lower()
    if extension not in SUPPORTED_SOURCE_EXTENSIONS:
        return build_status_record(source_path=source_path, status="unsupported_extension_deferred")

    if not converter_available(converter_command):
        return build_status_record(source_path=source_path, status="converter_missing_needs_local_ffmpeg")

    converted_path = allocate_converted_path(converted_dir, source_path)
    command = [
        *converter_command,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source_path),
        "-ac",
        "1",
        "-ar",
        "16000",
        str(converted_path),
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        return build_status_record(
            source_path=source_path,
            status="conversion_timeout_needs_review",
            error=redact_process_text(str(exc)),
        )

    if completed.returncode != 0 or not converted_path.exists():
        return build_status_record(
            source_path=source_path,
            status="conversion_failed_needs_review",
            error=redact_process_text((completed.stderr or completed.stdout or "ffmpeg conversion failed")),
        )

    capture_record = build_capture_record(
        source_path=source_path,
        converted_path=converted_path,
        language=language,
        label=label,
    )
    learning_queue = process_capture_record(capture_record, private_root=private_root)
    return build_status_record(
        source_path=source_path,
        status="converted_and_queued",
        converted_path=converted_path,
        learning_queue=learning_queue,
    )


def summarize_records(records: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "record_count": len(records),
        "converted_count": 0,
        "converter_missing_count": 0,
        "unsupported_count": 0,
        "failed_count": 0,
        "timeout_count": 0,
    }
    for record in records:
        status = record.get("conversion_status")
        if status == "converted_and_queued":
            counts["converted_count"] += 1
        elif status == "converter_missing_needs_local_ffmpeg":
            counts["converter_missing_count"] += 1
        elif status == "unsupported_extension_deferred":
            counts["unsupported_count"] += 1
        elif status == "conversion_failed_needs_review":
            counts["failed_count"] += 1
        elif status == "conversion_timeout_needs_review":
            counts["timeout_count"] += 1
    return counts


def run_conversion_batch(
    *,
    private_root: Path,
    input_dir: Path | None = None,
    converted_dir: Path | None = None,
    converter_command: list[str] | None = None,
    timeout_seconds: int = 20,
    language: str = "en",
    label: str = "tarik whatsapp voice note",
    include_unsupported: bool = False,
    limit: int | None = None,
) -> tuple[dict[str, Any], Path, Path]:
    source_dir, wav_dir, manifest_path, report_path = ensure_conversion_workspace(
        private_root,
        input_dir=input_dir,
        converted_dir=converted_dir,
    )
    command = converter_command or ["ffmpeg"]
    source_files = discover_audio_files(source_dir, include_unsupported=include_unsupported)
    if limit is not None:
        source_files = source_files[:limit]

    records = [
        convert_source_file(
            source_path,
            converted_dir=wav_dir,
            private_root=private_root,
            converter_command=command,
            timeout_seconds=timeout_seconds,
            language=language,
            label=label,
        )
        for source_path in source_files
    ]
    for record in records:
        append_jsonl(manifest_path, record)

    payload = {
        "voice_milestone": "VOICE-032",
        "source_extension_focus": SOURCE_EXTENSION_FOCUS,
        "supported_source_extensions": sorted(SUPPORTED_SOURCE_EXTENSIONS),
        "deferred_source_extensions": sorted(DEFERRED_SOURCE_EXTENSIONS),
        "private_root_relative": project_relative(private_root),
        "input_dir_relative": project_relative(source_dir),
        "converted_dir_relative": project_relative(wav_dir),
        "manifest_relative": project_relative(manifest_path),
        "report_relative": project_relative(report_path),
        "converter_command_name": command[0] if command else None,
        "converter_available": converter_available(command),
        "records": records,
        "summary": summarize_records(records),
        "privacy_boundary": conversion_privacy_boundary(),
    }
    return payload, manifest_path, report_path


def render_conversion_report(payload: dict[str, Any]) -> str:
    lines = [
        "# VOICE-032 Local Audio Conversion Report",
        "",
        "VOICE-032 converts selected local WhatsApp `.ogg` voice notes to WAV inside `data/private/`.",
        "",
        "## Summary",
        "",
        f"- Source extension focus: `{payload['source_extension_focus']}`",
        f"- Input folder: `{payload['input_dir_relative']}`",
        f"- Converted folder: `{payload['converted_dir_relative']}`",
        f"- Converter command: `{payload['converter_command_name']}`",
        f"- Converter available: `{payload['converter_available']}`",
        f"- Record count: `{payload['summary']['record_count']}`",
        f"- Converted count: `{payload['summary']['converted_count']}`",
        f"- Converter missing count: `{payload['summary']['converter_missing_count']}`",
        f"- Unsupported count: `{payload['summary']['unsupported_count']}`",
        f"- Failed count: `{payload['summary']['failed_count']}`",
        "",
        "## Records",
        "",
    ]
    if not payload["records"]:
        lines.append("- No `.ogg` files were found in the WhatsApp drop folder.")
    for record in payload["records"]:
        lines.append(
            f"- `{record['source_relative_path']}` -> `{record['conversion_status']}`"
        )
        if record.get("converted_relative_path"):
            lines.append(f"  converted: `{record['converted_relative_path']}`")
        if record.get("learning_queue"):
            lines.append(f"  queue: `{record['learning_queue']['processing_status']}`")
        if record.get("error"):
            lines.append(f"  error: `{record['error']}`")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- No provider calls.",
            "- No transcription.",
            "- No voice cloning.",
            "- No runtime profile application.",
            "- No public generated artifact from private audio.",
            "- Successful WAV conversions are passed into VOICE-030C for private local analysis.",
        ]
    )
    if payload["summary"]["converter_missing_count"]:
        lines.extend(
            [
                "",
                "## Local Tool Needed",
                "",
                "`ffmpeg` was not available for at least one `.ogg` file. Install or expose a local ffmpeg binary before converting WhatsApp exports.",
            ]
        )
    return "\n".join(lines) + "\n"
