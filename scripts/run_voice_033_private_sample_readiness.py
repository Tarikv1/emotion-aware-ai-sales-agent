#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from private_sample_readiness import (
    DEFAULT_PRIVATE_ROOT,
    REPORT_RELATIVE,
    RESULT_RELATIVE,
    ROOT,
    build_readiness_payload,
    ensure_private_root,
    render_readiness_report,
    write_json,
)


def resolve_project_path(value: str | None, default: Path) -> Path:
    if not value:
        return default
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report private Tarik speech-sample readiness for VOICE-030D.")
    parser.add_argument("--private-root", default=str(DEFAULT_PRIVATE_ROOT), help="Private Tarik speech-sample root.")
    parser.add_argument(
        "--allow-private-metadata-read",
        action="store_true",
        help="Required because this scans private file names, counts, and derived metadata.",
    )
    parser.add_argument("--print-json", action="store_true", help="Print the aggregate readiness payload.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    private_root = resolve_project_path(args.private_root, DEFAULT_PRIVATE_ROOT)
    try:
        ensure_private_root(private_root, allow_private_metadata_read=args.allow_private_metadata_read)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    payload = build_readiness_payload(private_root)
    result_path = private_root / RESULT_RELATIVE
    report_path = private_root / REPORT_RELATIVE
    write_json(result_path, payload)
    write_text(report_path, render_readiness_report(payload))

    if args.print_json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"VOICE-033 readiness status: {payload['readiness_status']}")
        print(f"Recommended action: {payload['next_action']['recommended_action']}")
        print(f"Private JSON: {payload['private_root_relative']}/{RESULT_RELATIVE.as_posix()}")
        print(f"Private report: {payload['private_root_relative']}/{REPORT_RELATIVE.as_posix()}")


if __name__ == "__main__":
    main()
