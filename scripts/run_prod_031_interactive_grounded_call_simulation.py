#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from prod_031_interactive_grounded_call_simulation import (
    DEFAULT_HTML,
    DEFAULT_REPORT,
    DEFAULT_RESULT,
    DEFAULT_TRACE,
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
            raise ValueError(f"PROD-031 path must stay inside project root: {path_text}") from exc
    if block_private and any(part.lower() in RESTRICTED_PARTS for part in resolved.parts):
        raise ValueError(f"PROD-031 path is restricted: {path_text}")
    return resolved


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the PROD-031 interactive grounded call simulation checkpoint.")
    parser.add_argument("--out", default=str(DEFAULT_RESULT), help="Result JSON output path.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT), help="Markdown report output path.")
    parser.add_argument("--trace-out", default=str(DEFAULT_TRACE), help="Interactive call traces JSON output path.")
    parser.add_argument("--html-out", default=str(DEFAULT_HTML), help="Static HTML trace output path.")
    args = parser.parse_args()

    out_path = resolve_path(args.out)
    report_path = resolve_path(args.report_out)
    trace_path = resolve_path(args.trace_out)
    html_path = resolve_path(args.html_out)

    payload, traces = build_payload(
        result_path=out_path,
        report_path=report_path,
        trace_path=trace_path,
        html_path=html_path,
    )
    write_json(out_path, payload)
    write_json(trace_path, traces)
    write_text(report_path, render_report(payload, traces))
    write_text(html_path, render_html(payload, traces))
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
