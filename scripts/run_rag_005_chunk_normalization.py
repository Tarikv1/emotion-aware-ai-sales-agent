#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from rag_chunk_normalization import normalize_chunks, render_chunk_report


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IMPORTS_DIR = ROOT / "research" / "experiments" / "generated" / "RAG-002-notebooklm-extraction-automation-bridge" / "imports"
DEFAULT_SOURCE_MANIFEST = ROOT / "research" / "experiments" / "generated" / "RAG-004-source-manifest-normalization" / "result.json"
DEFAULT_OUTPUT_DIR = ROOT / "research" / "experiments" / "generated" / "RAG-005-chunk-normalization"
DEFAULT_RESULT = DEFAULT_OUTPUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUTPUT_DIR / "report.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize NotebookLM report appendices into review-only RAG chunk candidates.")
    parser.add_argument("--imports-dir", default=str(DEFAULT_IMPORTS_DIR), help="Folder containing exported/pasted NotebookLM Markdown report files.")
    parser.add_argument("--source-manifest", default=str(DEFAULT_SOURCE_MANIFEST), help="RAG-004 source manifest JSON path.")
    parser.add_argument("--out", default=str(DEFAULT_RESULT), help="Output JSON chunk candidate path.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT), help="Output Markdown chunk candidate report path.")
    return parser.parse_args()


def resolve_path(path_value: str) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else ROOT / path


def main() -> None:
    args = parse_args()
    imports_dir = resolve_path(args.imports_dir)
    source_manifest = resolve_path(args.source_manifest)
    out_path = resolve_path(args.out)
    report_path = resolve_path(args.report_out)
    payload = normalize_chunks(imports_dir, source_manifest, root=ROOT)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(render_chunk_report(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))
    raise SystemExit(2 if payload["summary"]["secret_like_chunk_count"] else 0)


if __name__ == "__main__":
    main()
