#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from rag_quote_clearance_batches import build_quote_clearance_batches, render_quote_clearance_batches_report


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAG015_RESULT = ROOT / "research" / "experiments" / "generated" / "RAG-015-source-mapping-batches" / "result.json"
DEFAULT_RAG013_RESULT = ROOT / "research" / "experiments" / "generated" / "RAG-013-cleanup-strategy" / "result.json"
DEFAULT_RAG012_RESULT = ROOT / "research" / "experiments" / "generated" / "RAG-012-accepted-cleanup" / "result.json"
DEFAULT_RAG009_RESULT = ROOT / "research" / "experiments" / "generated" / "RAG-009-all-source-review-coverage" / "result.json"
DEFAULT_CASE = ROOT / "research" / "experiments" / "cases" / "rag-016-quote-clearance-batches.json"
DEFAULT_OUTPUT_DIR = ROOT / "research" / "experiments" / "generated" / "RAG-016-quote-clearance-batches"
DEFAULT_RESULT = DEFAULT_OUTPUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUTPUT_DIR / "report.md"
PRIVATE_PATH_PARTS = (("data", "private"), ("data", "private-restricted"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the RAG-016 quote-clearance batch packet.")
    parser.add_argument("--rag015-result", default=str(DEFAULT_RAG015_RESULT), help="RAG-015 batch JSON path.")
    parser.add_argument("--rag013-result", default=str(DEFAULT_RAG013_RESULT), help="RAG-013 cleanup strategy JSON path.")
    parser.add_argument("--rag012-result", default=str(DEFAULT_RAG012_RESULT), help="RAG-012 accepted cleanup JSON path.")
    parser.add_argument("--rag009-result", default=str(DEFAULT_RAG009_RESULT), help="RAG-009 coverage result JSON path.")
    parser.add_argument("--case", default=str(DEFAULT_CASE), help="RAG-016 case/config JSON path.")
    parser.add_argument("--out", default=str(DEFAULT_RESULT), help="Output JSON batch packet path.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT), help="Output Markdown batch report path.")
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
        raise ValueError(f"RAG-016 path must stay inside project root: {path_value}") from exc
    if _contains_private_path_parts(resolved):
        raise ValueError(f"RAG-016 path is restricted: {path_value}")
    return resolved


def main() -> None:
    args = parse_args()
    rag015_result = resolve_path(args.rag015_result)
    rag013_result = resolve_path(args.rag013_result)
    rag012_result = resolve_path(args.rag012_result)
    rag009_result = resolve_path(args.rag009_result)
    case_path = resolve_path(args.case)
    out_path = resolve_path(args.out)
    report_path = resolve_path(args.report_out)
    payload = build_quote_clearance_batches(
        rag015_result,
        rag013_result,
        rag012_result,
        rag009_result,
        case_path,
        root=ROOT,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(render_quote_clearance_batches_report(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
