#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from prod_041a_conditional_scenario_diversity_expansion import (
    DEFAULT_FRAMES,
    DEFAULT_PATTERN_BANK,
    DEFAULT_RECIPES,
    DEFAULT_REPORT,
    DEFAULT_RESULT,
    DEFAULT_SCENARIO_BANK,
    DEFAULT_SURFACE,
    DEFAULT_SURFACE_DATA,
    DEFAULT_TRACE,
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
            raise ValueError(f"PROD-041A path must stay inside project root: {path_text}") from exc
    if block_private and any(part.lower() in RESTRICTED_PARTS for part in resolved.parts):
        raise ValueError(f"PROD-041A path is restricted: {path_text}")
    return resolved


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the PROD-041A conditional scenario diversity expansion checkpoint.")
    parser.add_argument("--scenario-bank", default=str(DEFAULT_SCENARIO_BANK), help="PROD-014 scenario bank path.")
    parser.add_argument("--pattern-bank", default=str(DEFAULT_PATTERN_BANK), help="PROD-013 pattern bank path.")
    parser.add_argument("--out", default=str(DEFAULT_RESULT), help="Result JSON output path.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT), help="Markdown report output path.")
    parser.add_argument("--recipes-out", default=str(DEFAULT_RECIPES), help="Scenario recipes JSON output path.")
    parser.add_argument("--frames-out", default=str(DEFAULT_FRAMES), help="Concrete scenario frames JSON output path.")
    parser.add_argument("--trace-out", default=str(DEFAULT_TRACE), help="Scenario trace JSON output path.")
    parser.add_argument("--surface-out", default=str(DEFAULT_SURFACE), help="Static HTML surface output path.")
    parser.add_argument("--surface-data-out", default=str(DEFAULT_SURFACE_DATA), help="Static HTML data output path.")
    args = parser.parse_args()

    scenario_bank = resolve_path(args.scenario_bank)
    pattern_bank = resolve_path(args.pattern_bank)
    out_path = resolve_path(args.out)
    report_path = resolve_path(args.report_out)
    recipes_path = resolve_path(args.recipes_out)
    frames_path = resolve_path(args.frames_out)
    trace_path = resolve_path(args.trace_out)
    surface_path = resolve_path(args.surface_out)
    surface_data_path = resolve_path(args.surface_data_out)

    payload, recipes_payload, frames_payload, trace, surface_data = build_payload(
        scenario_bank_path=scenario_bank,
        pattern_bank_path=pattern_bank,
        result_path=out_path,
        report_path=report_path,
        recipes_path=recipes_path,
        frames_path=frames_path,
        trace_path=trace_path,
        surface_path=surface_path,
        surface_data_path=surface_data_path,
    )
    write_json(out_path, payload)
    write_json(recipes_path, recipes_payload)
    write_json(frames_path, frames_payload)
    write_json(trace_path, trace)
    write_json(surface_data_path, surface_data)
    write_text(report_path, render_report(payload, trace, frames_payload))
    write_text(surface_path, render_surface_html(payload, surface_data))
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
