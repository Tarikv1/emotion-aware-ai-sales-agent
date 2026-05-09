#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from prod_027_full_scenario_route_evaluation import (
    DEFAULT_CAMPAIGN_CASE_SOURCE,
    DEFAULT_CAMPAIGN_ID,
    DEFAULT_OUT_DIR,
    DEFAULT_REPORT,
    DEFAULT_RESULT,
    DEFAULT_SCENARIO_BANK,
    DEFAULT_SCENARIO_COUNT,
    DEFAULT_SCENARIO_SET,
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
            raise ValueError(f"PROD-027 path must stay inside project root: {path_text}") from exc
    if block_private and any(part.lower() in RESTRICTED_PARTS for part in resolved.parts):
        raise ValueError(f"PROD-027 path is restricted: {path_text}")
    return resolved


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the PROD-027 full scenario route evaluation checkpoint.")
    parser.add_argument("--scenario-bank", default=str(DEFAULT_SCENARIO_BANK), help="PROD-014 scenario-bank JSON path.")
    parser.add_argument("--campaign-case-source", default=str(DEFAULT_CAMPAIGN_CASE_SOURCE), help="Campaign case source path.")
    parser.add_argument("--campaign-id", default=DEFAULT_CAMPAIGN_ID, help="Campaign ID for the local guarded runtime.")
    parser.add_argument("--scenario-count", type=int, default=DEFAULT_SCENARIO_COUNT, help="Number of full scenarios to evaluate.")
    parser.add_argument("--out", default=str(DEFAULT_RESULT), help="Result JSON output path.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT), help="Markdown report output path.")
    parser.add_argument("--scenario-set-out", default=str(DEFAULT_SCENARIO_SET), help="Full scenario set JSON output path.")
    parser.add_argument("--html-out", default=str(DEFAULT_TRACE_HTML), help="Static HTML route trace output path.")
    args = parser.parse_args()

    out_path = resolve_path(args.out)
    report_path = resolve_path(args.report_out)
    scenario_set_path = resolve_path(args.scenario_set_out)
    html_path = resolve_path(args.html_out)
    scenario_bank_path = resolve_path(args.scenario_bank)
    campaign_case_source = resolve_path(args.campaign_case_source)

    if out_path.parent == DEFAULT_OUT_DIR:
        out_path.parent.mkdir(parents=True, exist_ok=True)

    payload, scenario_set = build_payload(
        scenario_bank_path,
        campaign_case_source=campaign_case_source,
        campaign_id=args.campaign_id,
        scenario_count=args.scenario_count,
        scenario_set_path=scenario_set_path,
        report_path=report_path,
        trace_html_path=html_path,
    )
    write_json(out_path, payload)
    write_json(scenario_set_path, scenario_set)
    write_text(report_path, render_report(payload))
    write_text(html_path, render_html(payload))
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
