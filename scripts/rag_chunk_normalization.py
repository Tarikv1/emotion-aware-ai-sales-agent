from __future__ import annotations

import csv
import hashlib
import json
import re
from io import StringIO
from pathlib import Path
from typing import Any

from rag_knowledge_base import ALLOWED_TOPIC_IDS, get_topic_taxonomy
from rag_report_import_readiness import infer_topic_ids, normalize_report_text
from rag_source_manifest_normalization import title_key


RAG_CHUNK_NORMALIZATION_ID = "RAG-005-chunk-normalization"

SECRET_RE = re.compile(
    r"sk-[A-Za-z0-9_-]{20,}|sk_car_[A-Za-z0-9_-]{12,}|xi-api-key\s*[:=]\s*[A-Za-z0-9]|"
    r"ELEVENLABS_API_KEY|OPENAI_API_KEY|CARTESIA_API_KEY|AIza[0-9A-Za-z_-]{20,}",
    re.IGNORECASE,
)

FIELD_ALIASES = {
    "chunk_id": "original_chunk_id",
    "stable_chunk_id": "original_chunk_id",
    "chunk id": "original_chunk_id",
    "source_title": "source_title",
    "source title": "source_title",
    "source_title_id": "source_title",
    "source title/id": "source_title",
    "source_id": "source_title",
    "source id": "source_title",
    "topic_id": "topic_id",
    "topic id": "topic_id",
    "topic": "topic_id",
    "language": "language",
    "sales_stage": "sales_stage",
    "sales stage": "sales_stage",
    "conversation_stage": "sales_stage",
    "principle": "principle",
    "tactic_name": "principle",
    "application": "application",
    "agent_goal": "application",
    "when_not_to_use": "when_not_to_use",
    "when not to use": "when_not_to_use",
    "example_phrase": "example_phrase",
    "example phrase": "example_phrase",
    "emotional_cues": "emotional_cues",
    "emotional cues": "emotional_cues",
    "customer_emotion": "emotional_cues",
    "compliance_notes": "compliance_notes",
    "compliance notes": "compliance_notes",
    "evidence_type": "evidence_type",
    "evidence type": "evidence_type",
    "confidence": "confidence",
    "citation_note": "citation_note",
    "citation note": "citation_note",
    "source_excerpt": "source_excerpt",
    "source_excerpt_present": "source_excerpt",
    "short_excerpt": "source_excerpt",
    "source excerpt present": "source_excerpt",
}

REQUIRED_REVIEW_FIELDS = (
    "source_title",
    "topic_id",
    "principle",
    "application",
    "when_not_to_use",
)

TOPIC_ORDER = {topic["topic_id"]: index for index, topic in enumerate(get_topic_taxonomy())}


def normalize_key(value: str) -> str:
    cleaned = normalize_report_text(value)
    cleaned = cleaned.strip().strip('"').strip("'")
    cleaned = re.sub(r"^\s*[-*]\s+", "", cleaned)
    cleaned = cleaned.lower().replace("-", "_")
    cleaned = re.sub(r"[^a-z0-9_ ]+", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def clean_value(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(clean_value(item) for item in value if clean_value(item))
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    text = normalize_report_text(str(value))
    text = text.replace("\\[", "[").replace("\\]", "]").replace('\\"', '"')
    text = text.replace("**", "").replace("`", "")
    text = re.sub(r"\s+", " ", text).strip(" \t\r\n,")
    return text.strip('"')


def csv_cells(line: str) -> list[str]:
    try:
        return [clean_value(cell) for cell in next(csv.reader(StringIO(line)))]
    except (csv.Error, StopIteration):
        return []


def canonical_field(key: str) -> str | None:
    normalized = normalize_key(key)
    return FIELD_ALIASES.get(normalized)


def rag_appendix_ranges(text: str) -> list[tuple[int, int]]:
    matches = list(re.finditer(r"(?im)^#{1,6}\s+.*RAG[-\s]?Ready.*(?:Appendix|Extraction)", text))
    if not matches:
        return [(0, len(text))]
    ranges: list[tuple[int, int]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        ranges.append((match.start(), end))
    return ranges


def subsection_for_chunks(text: str) -> str:
    ranges = rag_appendix_ranges(text)
    parts = [text[start:end] for start, end in ranges]
    return "\n".join(parts)


def parse_jsonish_chunk_blocks(section: str) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    lines = section.splitlines()
    current: dict[str, Any] | None = None
    for line in lines:
        normalized = normalize_report_text(line)
        if re.search(r'"?(?:stable_)?chunk_id"?\s*[:=]', normalized, re.IGNORECASE):
            if current:
                chunks.append(current)
            current = {}
        if current is None:
            continue
        match = re.match(r'\s*"?([A-Za-z0-9_ ]+)"?\s*[:=]\s*(.+?)\s*,?\s*$', normalized)
        if not match:
            continue
        field = canonical_field(match.group(1))
        if not field:
            continue
        value = clean_value(match.group(2))
        if field == "source_excerpt":
            current["source_excerpt_present"] = True
            continue
        current[field] = value
    if current:
        chunks.append(current)
    return chunks


def parse_row_content_chunks(section: str) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in section.splitlines():
        cells = csv_cells(normalize_report_text(line))
        if len(cells) < 2:
            continue
        field = canonical_field(cells[0])
        if not field:
            continue
        value = cells[1]
        if field == "original_chunk_id":
            if current:
                chunks.append(current)
            current = {}
        if current is None:
            continue
        if field == "source_excerpt":
            current["source_excerpt_present"] = True
            continue
        current[field] = value
    if current:
        chunks.append(current)
    return chunks


def chunk_fingerprint(chunk: dict[str, Any]) -> str:
    basis = "|".join(
        clean_value(chunk.get(field, ""))
        for field in ("source_title", "topic_id", "principle", "application", "citation_note")
    )
    return hashlib.sha1(basis.encode("utf-8")).hexdigest()[:12]


def load_source_manifest(path: Path | str) -> dict[str, Any]:
    manifest_path = Path(path)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    return payload.get("source_manifest", payload)


def build_source_lookup(source_manifest: dict[str, Any]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for source in source_manifest.get("sources", []):
        source_id = str(source.get("source_id", ""))
        for title in [source.get("canonical_title", ""), *source.get("raw_titles", [])]:
            key = title_key(str(title))
            if key and source_id:
                lookup[key] = source_id
    return lookup


def map_source_ids(source_title: str, source_lookup: dict[str, str]) -> list[str]:
    key = title_key(source_title)
    if key in source_lookup:
        return [source_lookup[key]]
    matches = []
    for candidate_key, source_id in source_lookup.items():
        if key and (key in candidate_key or candidate_key in key) and source_id not in matches:
            matches.append(source_id)
    return matches[:3]


def split_list_field(value: str) -> list[str]:
    if not value:
        return []
    text = value.strip()
    if text.startswith("[") and text.endswith("]"):
        text = text.strip("[]")
    return [clean_value(piece) for piece in re.split(r"\s*[,;/]\s*", text) if clean_value(piece)]


def normalize_chunk(
    raw: dict[str, Any],
    *,
    index: int,
    report_path: Path,
    report_topic_ids: list[str],
    source_lookup: dict[str, str],
    root: Path,
) -> dict[str, Any]:
    topic_id = clean_value(raw.get("topic_id", ""))
    source_title = clean_value(raw.get("source_title", ""))
    source_ids = map_source_ids(source_title, source_lookup)
    missing_fields = [
        field
        for field in REQUIRED_REVIEW_FIELDS
        if not clean_value(raw.get(field, ""))
    ]
    review_flags = []
    if missing_fields:
        review_flags.append("missing_required_fields")
    if not source_ids:
        review_flags.append("source_mapping_required")
    topic_ids = [topic_id] if topic_id in ALLOWED_TOPIC_IDS else report_topic_ids
    if topic_id and topic_id not in ALLOWED_TOPIC_IDS:
        review_flags.append("topic_mapping_required")
    if not topic_ids:
        review_flags.append("topic_mapping_required")
    if raw.get("source_excerpt_present"):
        review_flags.append("quote_review_required")
    if SECRET_RE.search(json.dumps(raw, ensure_ascii=False)):
        review_flags.append("secret_like_text_detected")
    fingerprint = chunk_fingerprint(raw)
    return {
        "chunk_candidate_id": f"rag005-chunk-{index:03d}",
        "stable_key": fingerprint,
        "original_chunk_id": clean_value(raw.get("original_chunk_id", "")),
        "source_title": source_title,
        "source_ids": source_ids,
        "source_mapping_status": "mapped" if source_ids else "needs_review",
        "topic_ids": topic_ids,
        "original_topic_id": topic_id,
        "language": clean_value(raw.get("language", "")),
        "sales_stage": clean_value(raw.get("sales_stage", "")),
        "principle": clean_value(raw.get("principle", "")),
        "application": clean_value(raw.get("application", "")),
        "when_not_to_use": clean_value(raw.get("when_not_to_use", "")),
        "example_phrases": split_list_field(clean_value(raw.get("example_phrase", ""))),
        "emotional_cues": split_list_field(clean_value(raw.get("emotional_cues", ""))),
        "compliance_notes": clean_value(raw.get("compliance_notes", "")),
        "evidence_type": clean_value(raw.get("evidence_type", "")),
        "confidence": clean_value(raw.get("confidence", "")),
        "citation_note": clean_value(raw.get("citation_note", "")),
        "source_excerpt_present": bool(raw.get("source_excerpt_present")),
        "source_excerpt_text_stored": False,
        "report_name": report_path.name,
        "report_path": rel_path(report_path, root),
        "review_status": "needs_human_review",
        "review_flags": review_flags or ["human_review_required"],
    }


def markdown_reports(import_dir: Path) -> list[Path]:
    if not import_dir.exists():
        return []
    return sorted(
        path
        for path in import_dir.glob("*.md")
        if path.is_file() and path.name.lower() != "readme.md"
    )


def rel_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def extract_raw_chunks_from_report(path: Path) -> list[dict[str, Any]]:
    text = normalize_report_text(path.read_text(encoding="utf-8-sig", errors="replace"))
    section = subsection_for_chunks(text)
    raw_chunks = parse_jsonish_chunk_blocks(section)
    raw_chunks.extend(parse_row_content_chunks(section))
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for raw in raw_chunks:
        fingerprint = chunk_fingerprint(raw)
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        unique.append(raw)
    return unique


def normalize_chunks(
    imports_dir: Path | str,
    source_manifest_path: Path | str,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    root_path = root or Path(__file__).resolve().parents[1]
    imports_path = Path(imports_dir)
    if not imports_path.is_absolute():
        imports_path = root_path / imports_path
    manifest_path = Path(source_manifest_path)
    if not manifest_path.is_absolute():
        manifest_path = root_path / manifest_path
    source_manifest = load_source_manifest(manifest_path)
    source_lookup = build_source_lookup(source_manifest)

    raw_entries: list[dict[str, Any]] = []
    reports_scanned: list[dict[str, Any]] = []
    for report_path in markdown_reports(imports_path):
        text = normalize_report_text(report_path.read_text(encoding="utf-8-sig", errors="replace"))
        topic_ids = infer_topic_ids(report_path, text)
        raw_chunks = extract_raw_chunks_from_report(report_path)
        reports_scanned.append(
            {
                "name": report_path.name,
                "path": rel_path(report_path, root_path),
                "topic_ids": topic_ids,
                "raw_chunk_count": len(raw_chunks),
            }
        )
        for raw in raw_chunks:
            raw_entries.append(
                {
                    "raw": raw,
                    "report_path": report_path,
                    "topic_ids": topic_ids,
                }
            )
    raw_entries.sort(
        key=lambda entry: (
            min((TOPIC_ORDER.get(topic_id, 999) for topic_id in entry["topic_ids"]), default=999),
            rel_path(entry["report_path"], root_path).lower(),
            chunk_fingerprint(entry["raw"]),
        )
    )
    chunk_candidates = [
        normalize_chunk(
            entry["raw"],
            index=index,
            report_path=entry["report_path"],
            report_topic_ids=entry["topic_ids"],
            source_lookup=source_lookup,
            root=root_path,
        )
        for index, entry in enumerate(raw_entries, start=1)
    ]

    mapped_count = sum(1 for chunk in chunk_candidates if chunk["source_ids"])
    chunks_requiring_review = [chunk for chunk in chunk_candidates if chunk["review_status"] == "needs_human_review"]
    chunks_with_excerpt = [chunk for chunk in chunk_candidates if chunk["source_excerpt_present"]]
    chunks_with_topic_mapping_review = [
        chunk
        for chunk in chunk_candidates
        if "topic_mapping_required" in chunk["review_flags"]
    ]
    secret_like_chunks = [
        chunk["chunk_candidate_id"]
        for chunk in chunk_candidates
        if "secret_like_text_detected" in chunk["review_flags"]
    ]
    summary = {
        "report_count": len(reports_scanned),
        "chunk_candidate_count": len(chunk_candidates),
        "mapped_chunk_count": mapped_count,
        "unmapped_chunk_count": len(chunk_candidates) - mapped_count,
        "chunks_requiring_review_count": len(chunks_requiring_review),
        "chunks_with_source_excerpt_count": len(chunks_with_excerpt),
        "topic_mapping_review_count": len(chunks_with_topic_mapping_review),
        "secret_like_chunk_count": len(secret_like_chunks),
        "source_excerpt_text_stored": False,
        "runtime_retrieval_enabled": False,
        "chunk_import_enabled": False,
        "external_provider_calls_made": False,
        "notebooklm_api_used": False,
        "raw_source_text_stored": False,
        "private_customer_data_used": False,
    }
    return {
        "normalization_id": RAG_CHUNK_NORMALIZATION_ID,
        "imports_dir": rel_path(imports_path, root_path),
        "source_manifest_path": rel_path(manifest_path, root_path),
        "summary": summary,
        "chunk_candidates": chunk_candidates,
        "reports_scanned": reports_scanned,
        "review_queues": {
            "unmapped_chunks": [
                chunk["chunk_candidate_id"]
                for chunk in chunk_candidates
                if not chunk["source_ids"]
            ],
            "chunks_with_source_excerpts": [
                chunk["chunk_candidate_id"]
                for chunk in chunks_with_excerpt
            ],
            "topic_mapping_review_chunks": [
                chunk["chunk_candidate_id"]
                for chunk in chunks_with_topic_mapping_review
            ],
            "secret_like_chunks": secret_like_chunks,
        },
        "boundaries": {
            "runtime_retrieval_enabled": False,
            "chunk_import_enabled": False,
            "notebooklm_api_used": False,
            "external_provider_calls_made": False,
            "private_customer_data_allowed": False,
            "raw_source_text_import_allowed": False,
            "source_excerpt_text_stored": False,
        },
    }


def render_chunk_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# RAG-005 Chunk Normalization",
        "",
        "This report converts NotebookLM report appendices into metadata-only chunk candidates for human review.",
        "",
        "Runtime retrieval remains disabled. RAG-005 does not import chunks into product memory, call providers, or make the sales agent use any extracted tactic.",
        "",
        "## Summary",
        "",
        f"- Reports scanned: `{summary['report_count']}`",
        f"- Chunk candidates: `{summary['chunk_candidate_count']}`",
        f"- Mapped chunks: `{summary['mapped_chunk_count']}`",
        f"- Unmapped chunks: `{summary['unmapped_chunk_count']}`",
        f"- Chunks requiring review: `{summary['chunks_requiring_review_count']}`",
        f"- Chunks with source excerpts flagged: `{summary['chunks_with_source_excerpt_count']}`",
        f"- Chunks requiring topic mapping review: `{summary['topic_mapping_review_count']}`",
        f"- Source excerpt text stored: `{summary['source_excerpt_text_stored']}`",
        f"- Runtime retrieval enabled: `{summary['runtime_retrieval_enabled']}`",
        f"- Chunk import enabled: `{summary['chunk_import_enabled']}`",
        "",
        "## Chunk Candidates",
        "",
        "| Candidate ID | Topic | Source IDs | Principle | Review Flags |",
        "| --- | --- | --- | --- | --- |",
    ]
    for chunk in payload["chunk_candidates"]:
        topic = ", ".join(chunk["topic_ids"]) or "needs_topic_review"
        sources = ", ".join(chunk["source_ids"]) or "needs_source_mapping"
        principle = chunk["principle"].replace("|", "/")[:100]
        flags = ", ".join(chunk["review_flags"])
        lines.append(f"| `{chunk['chunk_candidate_id']}` | {topic} | {sources} | {principle} | {flags} |")
    lines.extend(
        [
            "",
            "## Human Review Needed",
            "",
            "- Verify source mappings against the RAG-004 manifest.",
            "- Remove unsafe, manipulative, non-compliant, or product-inappropriate tactics.",
            "- Review any chunk with `quote_review_required`; source excerpt text is intentionally not copied forward.",
            "- Convert useful chunks into the final RAG schema only in a later checkpoint.",
            "",
            "## Boundaries",
            "",
            "- No runtime retrieval is enabled.",
            "- No chunk import into product memory is enabled.",
            "- No provider/API calls are made.",
            "- No source excerpt text is stored in RAG-005 outputs.",
            "",
        ]
    )
    return "\n".join(lines)
