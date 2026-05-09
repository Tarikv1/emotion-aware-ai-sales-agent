#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from prod_029_grounded_full_scenario_rerun import (
    DEFAULT_GROUNDING_CAMPAIGN,
    DEFAULT_REPORT,
    DEFAULT_RESULT,
    DEFAULT_SCENARIO_SET,
    DEFAULT_SOURCE_RESULT,
    DEFAULT_SOURCE_SCENARIO_SET,
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
            raise ValueError(f"PROD-029 path must stay inside project root: {path_text}") from exc
    if block_private and any(part.lower() in RESTRICTED_PARTS for part in resolved.parts):
        raise ValueError(f"PROD-029 path is restricted: {path_text}")
    return resolved


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the PROD-029 grounded full-scenario rerun checkpoint.")
    parser.add_argument("--source-result", default=str(DEFAULT_SOURCE_RESULT), help="PROD-027 result JSON path.")
    parser.add_argument("--source-scenario-set", default=str(DEFAULT_SOURCE_SCENARIO_SET), help="PROD-027 full scenario set JSON path.")
    parser.add_argument("--grounding-campaign", default=str(DEFAULT_GROUNDING_CAMPAIGN), help="PROD-028 synthetic campaign JSON path.")
    parser.add_argument("--out", default=str(DEFAULT_RESULT), help="Result JSON output path.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT), help="Markdown report output path.")
    parser.add_argument("--scenario-set-out", default=str(DEFAULT_SCENARIO_SET), help="Grounded scenario set JSON output path.")
    parser.add_argument("--html-out", default=str(DEFAULT_TRACE_HTML), help="Static HTML trace output path.")
    args = parser.parse_args()

    source_result = resolve_path(args.source_result)
    source_scenario_set = resolve_path(args.source_scenario_set)
    grounding_campaign = resolve_path(args.grounding_campaign)
    out_path = resolve_path(args.out)
    report_path = resolve_path(args.report_out)
    scenario_set_path = resolve_path(args.scenario_set_out)
    html_path = resolve_path(args.html_out)

    payload, scenario_set = build_payload(
        source_result_path=source_result,
        source_scenario_set_path=source_scenario_set,
        grounding_campaign_path=grounding_campaign,
        result_path=out_path,
        report_path=report_path,
        scenario_set_path=scenario_set_path,
        trace_html_path=html_path,
    )
    write_json(out_path, payload)
    write_json(scenario_set_path, scenario_set)
    write_text(report_path, render_report(payload))
    write_text(html_path, render_html(payload))
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
