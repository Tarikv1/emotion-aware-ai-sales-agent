#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from prod_037_local_interactive_trace_demo_surface import (
    DEFAULT_REPORT,
    DEFAULT_RESULT,
    DEFAULT_SOURCE_PACKET,
    DEFAULT_SURFACE,
    DEFAULT_SURFACE_DATA,
    ROOT,
    build_payload,
    render_report,
    render_surface_html,
    write_json,
    write_text,
)


RESTRICTED_PARTS = {"private", "private-restricted"}


def resolve_path(path_text: str, *, must_stay_in_root: bool = True, block_private: bool = True) -> Path:
    path = Path(path_text)
    if not path.is_absolute():
        path = ROOT / path
    resolved = path.resolve()
    if must_stay_in_root:
        try:
            resolved.relative_to(ROOT)
        except ValueError as exc:
            raise ValueError(f"PROD-037 path must stay inside project root: {path_text}") from exc
    if block_private and any(part.lower() in RESTRICTED_PARTS for part in resolved.parts):
        raise ValueError(f"PROD-037 path is restricted: {path_text}")
    return resolved


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the PROD-037 local interactive trace demo surface checkpoint.")
    parser.add_argument("--source-packet", default=str(DEFAULT_SOURCE_PACKET), help="PROD-036 readiness packet JSON path.")
    parser.add_argument("--out", default=str(DEFAULT_RESULT), help="Result JSON output path.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT), help="Markdown report output path.")
    parser.add_argument("--surface-out", default=str(DEFAULT_SURFACE), help="Static HTML trace demo surface output path.")
    parser.add_argument("--surface-data-out", default=str(DEFAULT_SURFACE_DATA), help="Trace demo surface data JSON output path.")
    args = parser.parse_args()

    source_packet = resolve_path(args.source_packet)
    out_path = resolve_path(args.out)
    report_path = resolve_path(args.report_out)
    surface_path = resolve_path(args.surface_out)
    surface_data_path = resolve_path(args.surface_data_out)

    payload, surface_data = build_payload(
        source_packet_path=source_packet,
        result_path=out_path,
        report_path=report_path,
        surface_path=surface_path,
        surface_data_path=surface_data_path,
    )
    write_json(out_path, payload)
    write_json(surface_data_path, surface_data)
    write_text(report_path, render_report(payload))
    write_text(surface_path, render_surface_html(payload, surface_data))
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
