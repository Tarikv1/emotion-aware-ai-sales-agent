#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from private_audio_conversion import (
    DEFAULT_PRIVATE_ROOT,
    ROOT,
    render_conversion_report,
    run_conversion_batch,
)


def resolve_project_path(value: str | None, default: Path | None = None) -> Path:
    if value:
        path = Path(value)
        return path if path.is_absolute() else ROOT / path
    if default is None:
        raise SystemExit("Missing required path.")
    return default


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert local WhatsApp .ogg voice notes to WAV under data/private/.")
    parser.add_argument("--private-root", default=str(DEFAULT_PRIVATE_ROOT), help="Private Tarik speech sample root.")
    parser.add_argument("--input-dir", help="Optional private input directory. Defaults to <private-root>/whatsapp-voice-notes.")
    parser.add_argument("--converted-dir", help="Optional private output directory. Defaults to <private-root>/converted-audio.")
    parser.add_argument(
        "--ffmpeg-command",
        nargs="+",
        default=["ffmpeg"],
        help="Converter command prefix. Defaults to ffmpeg. Tests may pass a local fake converter.",
    )
    parser.add_argument("--timeout-seconds", type=int, default=20, help="Per-file local conversion timeout.")
    parser.add_argument("--language", default="en", choices=["en", "de", "unknown"], help="Language label for queued WAVs.")
    parser.add_argument("--label", default="tarik whatsapp voice note", help="Private label for queued converted WAVs.")
    parser.add_argument("--include-unsupported", action="store_true", help="Record unsupported local formats as deferred.")
    parser.add_argument("--limit", type=int, help="Optional maximum number of source files to process.")
    parser.add_argument("--print-json", action="store_true", help="Print the private conversion payload.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    private_root = resolve_project_path(args.private_root, DEFAULT_PRIVATE_ROOT)
    input_dir = resolve_project_path(args.input_dir) if args.input_dir else None
    converted_dir = resolve_project_path(args.converted_dir) if args.converted_dir else None
    try:
        payload, _manifest_path, report_path = run_conversion_batch(
            private_root=private_root,
            input_dir=input_dir,
            converted_dir=converted_dir,
            converter_command=args.ffmpeg_command,
            timeout_seconds=args.timeout_seconds,
            language=args.language,
            label=args.label,
            include_unsupported=args.include_unsupported,
            limit=args.limit,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    write_text(report_path, render_conversion_report(payload))

    if args.print_json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"VOICE-032 checked {payload['summary']['record_count']} file(s).")
        print(f"Converted {payload['summary']['converted_count']} file(s).")
        if payload["summary"]["converter_missing_count"]:
            print("ffmpeg is missing for at least one .ogg file; install/expose ffmpeg locally before conversion.")
        print(f"Private report: {payload['report_relative']}")


if __name__ == "__main__":
    main()
