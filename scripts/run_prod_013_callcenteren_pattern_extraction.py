#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from callcenteren_pattern_extraction import ROOT, build_payload, render_report, write_json, write_text


DEFAULT_RAW_DIR = ROOT / "data" / "external" / "callcenteren" / "raw"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / "PROD-013-callcenteren-pattern-extraction"
DEFAULT_RESULT = DEFAULT_OUT_DIR / "pattern-bank.json"
DEFAULT_REPORT = DEFAULT_OUT_DIR / "report.md"


def resolve_project_path(path_text: str | None, default: Path) -> Path:
    path = Path(path_text) if path_text else default
    candidate = path if path.is_absolute() else ROOT / path
    resolved = candidate.resolve(strict=False)
    root = ROOT.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"PROD-013 path must stay inside project root: {path_text}") from exc
    return resolved


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract abstract CallCenterEN sales-call patterns into a safe local pattern bank.")
    parser.add_argument("--raw-dir", default=str(DEFAULT_RAW_DIR), help="Ignored local folder containing CallCenterEN JSON/JSONL/ZIP files.")
    parser.add_argument("--out", default=str(DEFAULT_RESULT), help="Output pattern-bank JSON path.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT), help="Output Markdown report path.")
    parser.add_argument("--max-conversations", type=int, default=1000, help="Maximum conversations to parse for this run. Use 0 to scan all local conversations.")
    parser.add_argument("--record-limit", type=int, default=5000, help="Maximum stored sample records per high-volume pattern category. Use 0 for unbounded records.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    raw_dir = resolve_project_path(args.raw_dir, DEFAULT_RAW_DIR)
    out_path = resolve_project_path(args.out, DEFAULT_RESULT)
    report_path = resolve_project_path(args.report_out, DEFAULT_REPORT)

    payload = build_payload(raw_dir, max_conversations=args.max_conversations, record_limit=args.record_limit)
    write_json(out_path, payload)
    write_text(report_path, render_report(payload))
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
