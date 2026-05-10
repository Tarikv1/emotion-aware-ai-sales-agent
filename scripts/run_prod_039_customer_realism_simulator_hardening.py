#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from prod_039_customer_realism_simulator_hardening import (
    DEFAULT_COMPARISON_HTML,
    DEFAULT_COMPARISON_PACKET,
    DEFAULT_HARDENED_TRACE,
    DEFAULT_REPORT,
    DEFAULT_RESULT,
    DEFAULT_SOURCE_REVIEW_PACKET,
    DEFAULT_SOURCE_SURFACE_DATA,
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
            raise ValueError(f"PROD-039 path must stay inside project root: {path_text}") from exc
    if block_private and any(part.lower() in RESTRICTED_PARTS for part in resolved.parts):
        raise ValueError(f"PROD-039 path is restricted: {path_text}")
    return resolved


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the PROD-039 customer realism simulator hardening checkpoint.")
    parser.add_argument("--source-review-packet", default=str(DEFAULT_SOURCE_REVIEW_PACKET), help="PROD-038 review packet path.")
    parser.add_argument("--source-surface-data", default=str(DEFAULT_SOURCE_SURFACE_DATA), help="PROD-037 surface data JSON path.")
    parser.add_argument("--out", default=str(DEFAULT_RESULT), help="Result JSON output path.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT), help="Markdown report output path.")
    parser.add_argument("--hardened-trace-out", default=str(DEFAULT_HARDENED_TRACE), help="Hardened trace JSON output path.")
    parser.add_argument("--comparison-packet-out", default=str(DEFAULT_COMPARISON_PACKET), help="Comparison packet JSON output path.")
    parser.add_argument("--comparison-html-out", default=str(DEFAULT_COMPARISON_HTML), help="Comparison HTML output path.")
    args = parser.parse_args()

    source_review_packet = resolve_path(args.source_review_packet)
    source_surface_data = resolve_path(args.source_surface_data)
    out_path = resolve_path(args.out)
    report_path = resolve_path(args.report_out)
    hardened_trace_path = resolve_path(args.hardened_trace_out)
    comparison_packet_path = resolve_path(args.comparison_packet_out)
    comparison_html_path = resolve_path(args.comparison_html_out)

    payload, hardened_trace, comparison_packet = build_payload(
        source_review_packet_path=source_review_packet,
        source_surface_data_path=source_surface_data,
        result_path=out_path,
        report_path=report_path,
        hardened_trace_path=hardened_trace_path,
        comparison_packet_path=comparison_packet_path,
        comparison_html_path=comparison_html_path,
    )
    write_json(out_path, payload)
    write_json(hardened_trace_path, hardened_trace)
    write_json(comparison_packet_path, comparison_packet)
    write_text(report_path, render_report(payload, comparison_packet))
    write_text(comparison_html_path, render_html(payload, comparison_packet))
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
