#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from prod_026_local_demo_trace_harness import (
    DEFAULT_REPORT,
    DEFAULT_RESULT,
    DEFAULT_SOURCE_PROD_025_RESULT,
    DEFAULT_TRACE_HTML,
    DEFAULT_TRACE_PACKET,
    ROOT,
    build_payload,
    build_trace_packet,
    render_html,
    render_report,
    write_json,
    write_text,
)


PRIVATE_PATH_PARTS = (("data", "private"), ("data", "private-restricted"))


def _contains_private_path_parts(path: Path) -> bool:
    parts = tuple(part.lower() for part in path.parts)
    for private_parts in PRIVATE_PATH_PARTS:
        for index in range(0, len(parts) - len(private_parts) + 1):
            if parts[index : index + len(private_parts)] == private_parts:
                return True
    return False


def resolve_path(path_text: str | None, default: Path, *, allow_missing: bool = True) -> Path:
    path = Path(path_text) if path_text else default
    candidate = path if path.is_absolute() else ROOT / path
    resolved = candidate.resolve(strict=False)
    root = ROOT.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"PROD-026 path must stay inside project root: {path_text}") from exc
    if _contains_private_path_parts(resolved):
        raise ValueError(f"PROD-026 path is restricted: {path_text}")
    if not allow_missing and not resolved.exists():
        raise FileNotFoundError(resolved)
    return resolved


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the PROD-026 local demo trace harness checkpoint.")
    parser.add_argument("--source-prod-025-result", default=str(DEFAULT_SOURCE_PROD_025_RESULT), help="PROD-025 result JSON path.")
    parser.add_argument("--out", default=str(DEFAULT_RESULT), help="Output JSON path.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT), help="Output Markdown report path.")
    parser.add_argument("--trace-packet-out", default=str(DEFAULT_TRACE_PACKET), help="Output trace packet JSON path.")
    parser.add_argument("--html-out", default=str(DEFAULT_TRACE_HTML), help="Output static HTML trace harness path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_prod_025_result = resolve_path(args.source_prod_025_result, DEFAULT_SOURCE_PROD_025_RESULT, allow_missing=False)
    out_path = resolve_path(args.out, DEFAULT_RESULT)
    report_path = resolve_path(args.report_out, DEFAULT_REPORT)
    trace_packet_path = resolve_path(args.trace_packet_out, DEFAULT_TRACE_PACKET)
    html_path = resolve_path(args.html_out, DEFAULT_TRACE_HTML)

    payload = build_payload(
        source_prod_025_result,
        report_path=report_path,
        trace_packet_path=trace_packet_path,
        trace_html_path=html_path,
    )
    write_json(out_path, payload)
    write_text(report_path, render_report(payload))
    write_json(trace_packet_path, build_trace_packet(payload))
    write_text(html_path, render_html(payload))
    print(json.dumps(payload["harness_summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
