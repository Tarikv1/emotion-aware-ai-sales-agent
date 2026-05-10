#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from prod_038_local_demo_surface_review import (
    DEFAULT_REPORT,
    DEFAULT_RESULT,
    DEFAULT_REVIEW_PACKET,
    DEFAULT_SOURCE_SURFACE_DATA,
    ROOT,
    build_payload,
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
            raise ValueError(f"PROD-038 path must stay inside project root: {path_text}") from exc
    if block_private and any(part.lower() in RESTRICTED_PARTS for part in resolved.parts):
        raise ValueError(f"PROD-038 path is restricted: {path_text}")
    return resolved


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the PROD-038 local demo surface review checkpoint.")
    parser.add_argument("--source-surface-data", default=str(DEFAULT_SOURCE_SURFACE_DATA), help="PROD-037 surface data JSON path.")
    parser.add_argument("--out", default=str(DEFAULT_RESULT), help="Result JSON output path.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT), help="Markdown report output path.")
    parser.add_argument("--review-packet-out", default=str(DEFAULT_REVIEW_PACKET), help="Review packet JSON output path.")
    args = parser.parse_args()

    source_surface_data = resolve_path(args.source_surface_data)
    out_path = resolve_path(args.out)
    report_path = resolve_path(args.report_out)
    review_packet_path = resolve_path(args.review_packet_out)

    payload, packet = build_payload(
        source_surface_data_path=source_surface_data,
        result_path=out_path,
        report_path=report_path,
        review_packet_path=review_packet_path,
    )
    write_json(out_path, payload)
    write_json(review_packet_path, packet)
    write_text(report_path, render_report(payload, packet))
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
