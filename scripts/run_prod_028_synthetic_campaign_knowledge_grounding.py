#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from prod_028_synthetic_campaign_knowledge_grounding import (
    DEFAULT_CAMPAIGN_OUT,
    DEFAULT_REPORT,
    DEFAULT_RESULT,
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
            raise ValueError(f"PROD-028 path must stay inside project root: {path_text}") from exc
    if block_private and any(part.lower() in RESTRICTED_PARTS for part in resolved.parts):
        raise ValueError(f"PROD-028 path is restricted: {path_text}")
    return resolved


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the PROD-028 synthetic campaign knowledge grounding checkpoint.")
    parser.add_argument("--out", default=str(DEFAULT_RESULT), help="Result JSON output path.")
    parser.add_argument("--campaign-out", default=str(DEFAULT_CAMPAIGN_OUT), help="Synthetic campaign JSON output path.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT), help="Markdown report output path.")
    parser.add_argument("--html-out", default=str(DEFAULT_TRACE_HTML), help="Static HTML trace output path.")
    args = parser.parse_args()

    out_path = resolve_path(args.out)
    campaign_path = resolve_path(args.campaign_out)
    report_path = resolve_path(args.report_out)
    html_path = resolve_path(args.html_out)

    payload = build_payload(
        result_path=out_path,
        report_path=report_path,
        campaign_path=campaign_path,
        trace_html_path=html_path,
    )
    write_json(out_path, payload)
    write_json(campaign_path, payload["synthetic_campaign"])
    write_text(report_path, render_report(payload))
    write_text(html_path, render_html(payload))
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
