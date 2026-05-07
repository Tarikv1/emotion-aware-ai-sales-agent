#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from rag_source_mapped_quote_followup import (
    build_source_mapped_quote_followup,
    render_source_mapped_quote_followup_report,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAG013_RESULT = ROOT / "research" / "experiments" / "generated" / "RAG-013-cleanup-strategy" / "result.json"
DEFAULT_RAG009_RESULT = ROOT / "research" / "experiments" / "generated" / "RAG-009-all-source-review-coverage" / "result.json"
DEFAULT_CASE = ROOT / "research" / "experiments" / "cases" / "rag-014-source-mapped-quote-followup.json"
DEFAULT_OUTPUT_DIR = ROOT / "research" / "experiments" / "generated" / "RAG-014-source-mapped-quote-followup"
DEFAULT_RESULT = DEFAULT_OUTPUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUTPUT_DIR / "report.md"
PRIVATE_PATH_PARTS = (("data", "private"), ("data", "private-restricted"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the RAG-014 source-mapped quote follow-up artifact.")
    parser.add_argument("--rag013-result", default=str(DEFAULT_RAG013_RESULT), help="RAG-013 cleanup strategy JSON path.")
    parser.add_argument("--rag009-result", default=str(DEFAULT_RAG009_RESULT), help="RAG-009 coverage result JSON path.")
    parser.add_argument("--case", default=str(DEFAULT_CASE), help="RAG-014 case/config JSON path.")
    parser.add_argument("--out", default=str(DEFAULT_RESULT), help="Output JSON review path.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT), help="Output Markdown review report path.")
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
        raise ValueError(f"RAG-014 path must stay inside project root: {path_value}") from exc
    if _contains_private_path_parts(resolved):
        raise ValueError(f"RAG-014 path is restricted: {path_value}")
    return resolved


def main() -> None:
    args = parse_args()
    rag013_result = resolve_path(args.rag013_result)
    rag009_result = resolve_path(args.rag009_result)
    case_path = resolve_path(args.case)
    out_path = resolve_path(args.out)
    report_path = resolve_path(args.report_out)
    payload = build_source_mapped_quote_followup(rag013_result, rag009_result, case_path, root=ROOT)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(render_source_mapped_quote_followup_report(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
