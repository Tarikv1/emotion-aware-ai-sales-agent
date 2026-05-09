#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from full_sale_scenario_grounding import build_prod_006_payload, render_prod_006_report


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASE = ROOT / "research" / "experiments" / "cases" / "prod-006-full-sale-scenario-grounding.json"
DEFAULT_OUTPUT_DIR = ROOT / "research" / "experiments" / "generated" / "PROD-006-full-sale-scenario-grounding"
DEFAULT_RESULT = DEFAULT_OUTPUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUTPUT_DIR / "report.md"
PRIVATE_PATH_PARTS = (("data", "private"), ("data", "private-restricted"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the PROD-006 full-sale scenario grounding packet.")
    parser.add_argument("--case", default=str(DEFAULT_CASE), help="PROD-006 case JSON path.")
    parser.add_argument("--out", default=str(DEFAULT_RESULT), help="Output JSON path.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT), help="Output Markdown report path.")
    parser.add_argument(
        "--raw-zip-dir",
        default="",
        help="Optional ignored local ZIP directory for transient leakage scanning. No transcript text is written.",
    )
    return parser.parse_args()


def _contains_private_path_parts(path: Path) -> bool:
    parts = tuple(part.lower() for part in path.parts)
    for private_parts in PRIVATE_PATH_PARTS:
        for index in range(0, len(parts) - len(private_parts) + 1):
            if parts[index : index + len(private_parts)] == private_parts:
                return True
    return False


def resolve_project_path(path_value: str) -> Path:
    path = Path(path_value)
    candidate = path if path.is_absolute() else ROOT / path
    resolved = candidate.resolve(strict=False)
    root = ROOT.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"PROD-006 path must stay inside project root: {path_value}") from exc
    if _contains_private_path_parts(resolved):
        raise ValueError(f"PROD-006 path is restricted: {path_value}")
    return resolved


def main() -> None:
    args = parse_args()
    case_path = resolve_project_path(args.case)
    out_path = resolve_project_path(args.out)
    report_path = resolve_project_path(args.report_out)
    raw_zip_dir = resolve_project_path(args.raw_zip_dir) if args.raw_zip_dir else None
    payload = build_prod_006_payload(case_path, root=ROOT, raw_zip_dir=raw_zip_dir)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(render_prod_006_report(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
