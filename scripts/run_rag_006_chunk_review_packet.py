#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from rag_chunk_review_packet import build_review_packet, render_review_packet_report


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAG005_RESULT = ROOT / "research" / "experiments" / "generated" / "RAG-005-chunk-normalization" / "result.json"
DEFAULT_SOURCE_MANIFEST = ROOT / "research" / "experiments" / "generated" / "RAG-004-source-manifest-normalization" / "result.json"
DEFAULT_OUTPUT_DIR = ROOT / "research" / "experiments" / "generated" / "RAG-006-chunk-review-packet"
DEFAULT_RESULT = DEFAULT_OUTPUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUTPUT_DIR / "report.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build human review queues for RAG-005 chunk candidates.")
    parser.add_argument("--rag005-result", default=str(DEFAULT_RAG005_RESULT), help="RAG-005 chunk-normalization result JSON path.")
    parser.add_argument("--source-manifest", default=str(DEFAULT_SOURCE_MANIFEST), help="RAG-004 source manifest JSON path.")
    parser.add_argument("--out", default=str(DEFAULT_RESULT), help="Output JSON review packet path.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT), help="Output Markdown review packet report path.")
    return parser.parse_args()


def resolve_path(path_value: str) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else ROOT / path


def main() -> None:
    args = parse_args()
    rag005_result = resolve_path(args.rag005_result)
    source_manifest = resolve_path(args.source_manifest)
    out_path = resolve_path(args.out)
    report_path = resolve_path(args.report_out)
    payload = build_review_packet(rag005_result, source_manifest, root=ROOT)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(render_review_packet_report(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
