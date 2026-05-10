#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from prod_034_interactive_post_fix_review import (
    DEFAULT_PACKET,
    DEFAULT_REPORT,
    DEFAULT_RESULT,
    DEFAULT_SOURCE_RESULT,
    DEFAULT_SOURCE_TRACE,
    DEFAULT_TRACE_HTML,
    ROOT,
    build_payload,
    render_html,
    render_report,
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
            raise ValueError(f"PROD-034 path must stay inside project root: {path_text}") from exc
    if block_private and any(part.lower() in RESTRICTED_PARTS for part in resolved.parts):
        raise ValueError(f"PROD-034 path is restricted: {path_text}")
    return resolved


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the PROD-034 interactive post-fix review checkpoint.")
    parser.add_argument("--source-result", default=str(DEFAULT_SOURCE_RESULT), help="PROD-033 result JSON path.")
    parser.add_argument("--source-trace", default=str(DEFAULT_SOURCE_TRACE), help="PROD-033 interactive trace JSON path.")
    parser.add_argument("--out", default=str(DEFAULT_RESULT), help="Result JSON output path.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT), help="Markdown report output path.")
    parser.add_argument("--packet-out", default=str(DEFAULT_PACKET), help="Review packet JSON output path.")
    parser.add_argument("--html-out", default=str(DEFAULT_TRACE_HTML), help="Static HTML review output path.")
    args = parser.parse_args()

    source_result = resolve_path(args.source_result)
    source_trace = resolve_path(args.source_trace)
    out_path = resolve_path(args.out)
    report_path = resolve_path(args.report_out)
    packet_path = resolve_path(args.packet_out)
    html_path = resolve_path(args.html_out)

    payload, packet = build_payload(
        source_result_path=source_result,
        source_trace_path=source_trace,
        result_path=out_path,
        report_path=report_path,
        packet_path=packet_path,
        trace_html_path=html_path,
    )
    write_json(out_path, payload)
    write_json(packet_path, packet)
    write_text(report_path, render_report(payload, packet))
    write_text(html_path, render_html(payload, packet))
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
