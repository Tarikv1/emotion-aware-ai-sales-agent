#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from callcenteren_scenario_evaluation import (
    DEFAULT_RETRIEVAL_REGISTRY,
    ROOT,
    build_payload,
    render_report,
    write_json,
    write_text,
)


DEFAULT_CASES = ROOT / "research" / "experiments" / "cases" / "prod-012-callcenteren-scenario-evaluation.json"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / "PROD-012-callcenteren-scenario-evaluation"
DEFAULT_RESULT = DEFAULT_OUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUT_DIR / "report.md"
DEFAULT_RAW_ZIP_DIR = ROOT / "data" / "external" / "callcenteren" / "raw"
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
        raise ValueError(f"PROD-012 path must stay inside project root: {path_text}") from exc
    if _contains_private_path_parts(resolved):
        raise ValueError(f"PROD-012 path is restricted: {path_text}")
    if not allow_missing and not resolved.exists():
        raise FileNotFoundError(resolved)
    return resolved


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the PROD-012 CallCenterEN scenario evaluation.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="PROD-012 case JSON.")
    parser.add_argument("--registry", default=str(DEFAULT_RETRIEVAL_REGISTRY), help="RAG-017 runtime knowledge registry JSON.")
    parser.add_argument("--raw-zip-dir", default=str(DEFAULT_RAW_ZIP_DIR), help="Optional ignored local CallCenterEN ZIP drop folder.")
    parser.add_argument("--out", default=str(DEFAULT_RESULT), help="Output JSON path.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT), help="Output Markdown report path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cases_path = resolve_path(args.cases, DEFAULT_CASES, allow_missing=False)
    registry_path = resolve_path(args.registry, DEFAULT_RETRIEVAL_REGISTRY, allow_missing=False)
    raw_zip_dir = resolve_path(args.raw_zip_dir, DEFAULT_RAW_ZIP_DIR, allow_missing=True)
    out_path = resolve_path(args.out, DEFAULT_RESULT)
    report_path = resolve_path(args.report_out, DEFAULT_REPORT)

    payload = build_payload(cases_path, registry_path=registry_path, raw_zip_dir=raw_zip_dir)
    write_json(out_path, payload)
    write_text(report_path, render_report(payload))
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
