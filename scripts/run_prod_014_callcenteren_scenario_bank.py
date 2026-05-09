#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from callcenteren_scenario_bank import (
    DEFAULT_SCENARIO_COUNT,
    DEFAULT_PATTERN_BANK,
    DEFAULT_RAW_ZIP_DIR,
    ROOT,
    build_payload,
    render_report,
    write_json,
    write_text,
)


DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / "PROD-014-callcenteren-scenario-bank"
DEFAULT_RESULT = DEFAULT_OUT_DIR / "scenario-bank.json"
DEFAULT_REPORT = DEFAULT_OUT_DIR / "report.md"
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
        raise ValueError(f"PROD-014 path must stay inside project root: {path_text}") from exc
    if _contains_private_path_parts(resolved):
        raise ValueError(f"PROD-014 path is restricted: {path_text}")
    if not allow_missing and not resolved.exists():
        raise FileNotFoundError(resolved)
    return resolved


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a leakage-safe scenario bank from PROD-013 CallCenterEN abstract patterns.")
    parser.add_argument("--pattern-bank", default=str(DEFAULT_PATTERN_BANK), help="PROD-013 pattern-bank JSON path.")
    parser.add_argument("--raw-zip-dir", default=str(DEFAULT_RAW_ZIP_DIR), help="Optional ignored local CallCenterEN ZIP folder for transient leakage scans.")
    parser.add_argument("--out", default=str(DEFAULT_RESULT), help="Output scenario-bank JSON path.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT), help="Output Markdown report path.")
    parser.add_argument("--scenario-count", type=int, default=DEFAULT_SCENARIO_COUNT, help="Number of scenario packets to generate.")
    parser.add_argument("--leakage-sentence-limit", type=int, default=5000, help="Maximum transient source sentences used for leakage scan.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pattern_bank = resolve_path(args.pattern_bank, DEFAULT_PATTERN_BANK, allow_missing=False)
    raw_zip_dir = resolve_path(args.raw_zip_dir, DEFAULT_RAW_ZIP_DIR, allow_missing=True)
    out_path = resolve_path(args.out, DEFAULT_RESULT)
    report_path = resolve_path(args.report_out, DEFAULT_REPORT)

    payload = build_payload(
        pattern_bank,
        scenario_count=args.scenario_count,
        raw_zip_dir=raw_zip_dir,
        leakage_sentence_limit=args.leakage_sentence_limit,
    )
    write_json(out_path, payload)
    write_text(report_path, render_report(payload))
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
