#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from rag_all_source_review_coverage import build_all_source_review_coverage, render_all_source_review_coverage_report


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAG004_RESULT = ROOT / "research" / "experiments" / "generated" / "RAG-004-source-manifest-normalization" / "result.json"
DEFAULT_RAG005_RESULT = ROOT / "research" / "experiments" / "generated" / "RAG-005-chunk-normalization" / "result.json"
DEFAULT_RAG006_PACKET = ROOT / "research" / "experiments" / "generated" / "RAG-006-chunk-review-packet" / "result.json"
DEFAULT_RAG007_RESULT = ROOT / "research" / "experiments" / "generated" / "RAG-007-reviewed-first-slice" / "result.json"
DEFAULT_CASE = ROOT / "research" / "experiments" / "cases" / "rag-009-all-source-review-coverage.json"
DEFAULT_OUTPUT_DIR = ROOT / "research" / "experiments" / "generated" / "RAG-009-all-source-review-coverage"
DEFAULT_RESULT = DEFAULT_OUTPUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUTPUT_DIR / "report.md"
PRIVATE_PATH_PARTS = (("data", "private"), ("data", "private-restricted"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the RAG-009 all-source review coverage packet.")
    parser.add_argument("--rag004-result", default=str(DEFAULT_RAG004_RESULT), help="RAG-004 source manifest JSON path.")
    parser.add_argument("--rag005-result", default=str(DEFAULT_RAG005_RESULT), help="RAG-005 chunk normalization JSON path.")
    parser.add_argument("--rag006-packet", default=str(DEFAULT_RAG006_PACKET), help="RAG-006 chunk review packet JSON path.")
    parser.add_argument("--rag007-result", default=str(DEFAULT_RAG007_RESULT), help="RAG-007 reviewed first slice JSON path.")
    parser.add_argument("--case", default=str(DEFAULT_CASE), help="RAG-009 case/config JSON path.")
    parser.add_argument("--out", default=str(DEFAULT_RESULT), help="Output JSON coverage result path.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT), help="Output Markdown coverage report path.")
    return parser.parse_args()


def _contains_private_path_parts(path: Path) -> bool:
    parts = tuple(part.lower() for part in path.parts)
    for private_parts in PRIVATE_PATH_PARTS:
        for index in range(0, len(parts) - len(private_parts) + 1):
            if parts[index : index + len(private_parts)] == private_parts:
                return True
    return False


def resolve_path(path_value: str) -> Path:
    path = Path(path_value)
    candidate = path if path.is_absolute() else ROOT / path
    resolved = candidate.resolve(strict=False)
    root = ROOT.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"RAG-009 path must stay inside project root: {path_value}") from exc
    if _contains_private_path_parts(resolved):
        raise ValueError(f"RAG-009 path is restricted: {path_value}")
    return resolved


def main() -> None:
    args = parse_args()
    rag004_result = resolve_path(args.rag004_result)
    rag005_result = resolve_path(args.rag005_result)
    rag006_packet = resolve_path(args.rag006_packet)
    rag007_result = resolve_path(args.rag007_result)
    case_path = resolve_path(args.case)
    out_path = resolve_path(args.out)
    report_path = resolve_path(args.report_out)
    payload = build_all_source_review_coverage(
        rag004_result,
        rag005_result,
        rag006_packet,
        rag007_result,
        case_path,
        root=ROOT,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(render_all_source_review_coverage_report(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
