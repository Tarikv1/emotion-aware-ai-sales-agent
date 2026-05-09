#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from callcenteren_runtime_comparison import (
    DEFAULT_CAMPAIGN_CASE_SOURCE,
    DEFAULT_CAMPAIGN_ID,
    DEFAULT_LIMIT_SCENARIOS,
    DEFAULT_RAW_ZIP_DIR,
    DEFAULT_RETRIEVAL_REGISTRY,
    DEFAULT_SCENARIO_BANK,
    ROOT,
    build_payload,
    render_report,
    write_json,
    write_text,
)


DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / "PROD-015-callcenteren-runtime-comparison"
DEFAULT_RESULT = DEFAULT_OUT_DIR / "result.json"
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
        raise ValueError(f"PROD-015 path must stay inside project root: {path_text}") from exc
    if _contains_private_path_parts(resolved):
        raise ValueError(f"PROD-015 path is restricted: {path_text}")
    if not allow_missing and not resolved.exists():
        raise FileNotFoundError(resolved)
    return resolved


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run PROD-015 old-runtime vs retrieval-runtime comparison on the PROD-014 scenario bank.")
    parser.add_argument("--scenario-bank", default=str(DEFAULT_SCENARIO_BANK), help="PROD-014 scenario-bank JSON path.")
    parser.add_argument("--registry", default=str(DEFAULT_RETRIEVAL_REGISTRY), help="RAG-017 runtime knowledge registry JSON.")
    parser.add_argument("--campaign-cases", default=str(DEFAULT_CAMPAIGN_CASE_SOURCE), help="Campaign case wrapper containing runtime campaign definitions.")
    parser.add_argument("--campaign-id", default=DEFAULT_CAMPAIGN_ID, help="Runtime campaign ID used for generated English scenario prompts.")
    parser.add_argument("--limit-scenarios", type=int, default=DEFAULT_LIMIT_SCENARIOS, help="Stratified scenario limit. Use 0 for the full bank.")
    parser.add_argument("--raw-zip-dir", default=str(DEFAULT_RAW_ZIP_DIR), help="Optional ignored local CallCenterEN ZIP folder for transient leakage scans.")
    parser.add_argument("--leakage-sentence-limit", type=int, default=5000, help="Maximum transient source sentences used for leakage scan.")
    parser.add_argument("--out", default=str(DEFAULT_RESULT), help="Output JSON path.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT), help="Output Markdown report path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    scenario_bank = resolve_path(args.scenario_bank, DEFAULT_SCENARIO_BANK, allow_missing=False)
    registry_path = resolve_path(args.registry, DEFAULT_RETRIEVAL_REGISTRY, allow_missing=False)
    campaign_cases = resolve_path(args.campaign_cases, DEFAULT_CAMPAIGN_CASE_SOURCE, allow_missing=False)
    raw_zip_dir = resolve_path(args.raw_zip_dir, DEFAULT_RAW_ZIP_DIR, allow_missing=True)
    out_path = resolve_path(args.out, DEFAULT_RESULT)
    report_path = resolve_path(args.report_out, DEFAULT_REPORT)

    payload = build_payload(
        scenario_bank,
        registry_path=registry_path,
        campaign_case_source=campaign_cases,
        campaign_id=args.campaign_id,
        limit_scenarios=args.limit_scenarios,
        raw_zip_dir=raw_zip_dir,
        leakage_sentence_limit=args.leakage_sentence_limit,
    )
    write_json(out_path, payload)
    write_text(report_path, render_report(payload))
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
