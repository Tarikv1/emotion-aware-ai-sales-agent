from __future__ import annotations

import csv
import hashlib
import re
from collections import defaultdict
from io import StringIO
from pathlib import Path
from typing import Any

from rag_knowledge_base import get_topic_taxonomy
from rag_report_import_readiness import infer_topic_ids, normalize_report_text


RAG_SOURCE_MANIFEST_ID = "RAG-004-source-manifest-normalization"

SECRET_RE = re.compile(
    r"sk-[A-Za-z0-9_-]{20,}|sk_car_[A-Za-z0-9_-]{12,}|xi-api-key\s*[:=]\s*[A-Za-z0-9]|"
    r"ELEVENLABS_API_KEY|OPENAI_API_KEY|CARTESIA_API_KEY|AIza[0-9A-Za-z_-]{20,}",
    re.IGNORECASE,
)

SOURCE_FIELD_RE = re.compile(
    r"(?im)(?:source\\?_title\\?_id|source\\?_id|source\s+title/id|source\s+name/id)\s*[:=]\s*\"?([^\"\n\r,}{]+)"
)

SOURCE_HINT_RE = re.compile(
    r"youtube|transcript|blog|book|paper|arxiv|website|guide|masterclass|course|hubspot|"
    r"salesforce|pipedrive|cognism|ringcentral|stanford|nielsen|norman|cialdini|"
    r"telefonakquise|leitfaden|podcast|video|bigspeak|psychology today",
    re.IGNORECASE,
)

GENERIC_OR_HEADER_RE = re.compile(
    r"^(source|source\s+title|source\s+name/id|specific\s+source|citation|topic|language|"
    r"confidence|high|medium|low|evidence\s+density|primary\s+topic|main\s+contribution|"
    r"report\s+title|end:\s+complete|need_continuation|completion_status|coverage_checklist)$",
    re.IGNORECASE,
)

TOPIC_LABELS = {topic["topic_id"]: topic["label"] for topic in get_topic_taxonomy()}
KNOWN_SINGLE_WORD_SOURCES = {
    "bigspeak",
    "cognism",
    "hubspot",
    "mindtools",
    "pipedrive",
    "salesforce",
    "weclapp",
}


def slugify(value: str) -> str:
    value = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE)
    value = re.sub(r"[\s_-]+", "-", value.strip().lower())
    return value.strip("-") or "source"


def normalize_title(value: str) -> str:
    cleaned = normalize_report_text(value)
    cleaned = cleaned.replace("**", "").replace("*", "").replace("`", "")
    cleaned = cleaned.replace("\\", "")
    cleaned = re.sub(r"\[[^\]]*\]\([^)]+\)", "", cleaned)
    cleaned = re.sub(r"^\s*[-*]\s+", "", cleaned)
    cleaned = re.sub(r"^\s*\d+[.)]\s+", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" \t\r\n|;:,")
    cleaned = cleaned.strip('"')
    return cleaned


def title_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", normalize_title(value).lower())


def is_valid_source_title(value: str) -> bool:
    title = normalize_title(value)
    if not title:
        return False
    if len(title) < 4 or len(title) > 150:
        return False
    if "..." in title or "404" in title.lower() or "not found" in title.lower():
        return False
    if title[0].islower():
        return False
    if GENERIC_OR_HEADER_RE.match(title):
        return False
    lowered = title.lower()
    if lowered.split()[0] in {"i", "i'm", "could", "before", "just", "let's", "you"}:
        return False
    if len(title.split()) == 1 and lowered not in KNOWN_SINGLE_WORD_SOURCES:
        return False
    if any(marker in lowered for marker in ["chunk_id", "topic_id", "coverage_checklist", "completion_status"]):
        return False
    if re.match(r"^[a-z_ -]{3,32}\s*:", lowered):
        return False
    if lowered in {
        "application",
        "category",
        "chunk id",
        "citation note",
        "compliance notes",
        "conversation stage",
        "source id",
        "source title/id",
    }:
        return False
    if title.count(" ") > 18 and not SOURCE_HINT_RE.search(title):
        return False
    return True


def split_source_cell(value: str) -> list[str]:
    value = value.replace(" and ", "; ")
    pieces = re.split(r"\s*(?:;|\s\|\s| / |, and )\s*", value)
    return [normalize_title(piece) for piece in pieces if is_valid_source_title(piece)]


def csv_cells(line: str) -> list[str]:
    try:
        row = next(csv.reader(StringIO(line)))
    except (csv.Error, StopIteration):
        return []
    return [normalize_title(cell) for cell in row]


def source_column_indexes(cells: list[str]) -> list[int]:
    indexes: list[int] = []
    for index, cell in enumerate(cells):
        lowered = cell.lower()
        if "source type" in lowered or "citation" in lowered:
            continue
        if lowered in {"source", "source title", "source name/id", "source name", "source title/id", "specific source", "specific source(s)", "specific sources"}:
            indexes.append(index)
        elif "source title" in lowered or "source name" in lowered:
            indexes.append(index)
    return indexes


def extract_markdown_table_sources(lines: list[str]) -> list[str]:
    candidates: list[str] = []
    current_header: list[str] | None = None
    source_indexes: list[int] = []
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|") or "|" not in stripped[1:]:
            current_header = None
            source_indexes = []
            continue
        cells = [normalize_title(cell) for cell in stripped.strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells):
            continue
        lower_cells = [cell.lower() for cell in cells]
        if any("source" in cell for cell in lower_cells):
            current_header = cells
            source_indexes = source_column_indexes(cells)
            continue
        if current_header and source_indexes:
            for index in source_indexes:
                if index < len(cells):
                    candidates.extend(split_source_cell(cells[index]))
    return candidates


def extract_csv_like_sources(lines: list[str]) -> list[str]:
    candidates: list[str] = []
    active_source_columns: list[int] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "," not in stripped:
            continue
        if re.match(r'^"?[a-z_ -]{3,32}"?\s*:', stripped, re.IGNORECASE):
            continue
        cells = csv_cells(stripped)
        if len(cells) < 2:
            continue
        lower_cells = [cell.lower() for cell in cells]
        if any("source" in cell for cell in lower_cells):
            active_source_columns = source_column_indexes(cells)
            continue
        if active_source_columns:
            for index in active_source_columns:
                if index < len(cells):
                    candidates.extend(split_source_cell(cells[index]))
            continue
        first_cell = cells[0]
        if SOURCE_HINT_RE.search(first_cell):
            candidates.extend(split_source_cell(first_cell))
    return candidates


def extract_field_sources(text: str) -> list[str]:
    candidates: list[str] = []
    for match in SOURCE_FIELD_RE.finditer(text):
        raw = match.group(1)
        candidates.extend(split_source_cell(raw))
    return candidates


def source_coverage_lines(lines: list[str]) -> list[str]:
    sections: list[str] = []
    in_section = False
    for line in lines:
        if re.match(r"^#{1,6}\s+", line):
            in_section = bool(re.search(r"source\s+coverage|coverage\s+(?:table|matrix)", line, re.IGNORECASE))
            if in_section:
                sections.append(line)
            continue
        if in_section:
            sections.append(line)
    return sections


def extract_source_candidates(text: str) -> list[str]:
    normalized = normalize_report_text(text)
    lines = normalized.splitlines()
    coverage_lines = source_coverage_lines(lines)
    candidates: list[str] = []
    candidates.extend(extract_field_sources(normalized))
    candidates.extend(extract_markdown_table_sources(coverage_lines))
    candidates.extend(extract_csv_like_sources(coverage_lines))
    seen: set[str] = set()
    unique: list[str] = []
    for candidate in candidates:
        key = title_key(candidate)
        if key and key not in seen and is_valid_source_title(candidate):
            seen.add(key)
            unique.append(candidate)
    return unique


def guess_source_type(title: str) -> str:
    lower = title.lower()
    if "youtube" in lower or "video" in lower or "transcript" in lower or "masterclass" in lower or "course" in lower:
        return "video_or_transcript"
    if "blog" in lower or "website" in lower or "hubspot" in lower or "pipedrive" in lower or "cognism" in lower:
        return "website_or_blog"
    if "book" in lower:
        return "book"
    if "paper" in lower or "arxiv" in lower or "stanford" in lower:
        return "paper_or_reference"
    return "needs_review"


def guess_language(title: str) -> str:
    lower = title.lower()
    if any(term in lower for term in ["telefonakquise", "leitfaden", "guten tag", "lars krüger", "jens löser"]):
        return "de"
    return "mixed"


def stable_hash(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:10]


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


def build_source_manifest(import_dir: Path | str, *, root: Path | None = None) -> dict[str, Any]:
    root_path = root or Path(__file__).resolve().parents[1]
    imports_path = Path(import_dir)
    if not imports_path.is_absolute():
        imports_path = root_path / imports_path

    grouped: dict[str, dict[str, Any]] = {}
    reports_scanned: list[dict[str, Any]] = []
    secret_like_sources: set[str] = set()

    for report_path in markdown_reports(imports_path):
        text = report_path.read_text(encoding="utf-8-sig", errors="replace")
        normalized = normalize_report_text(text)
        topic_ids = infer_topic_ids(report_path, normalized)
        candidates = extract_source_candidates(normalized)
        reports_scanned.append(
            {
                "name": report_path.name,
                "path": rel_path(report_path, root_path),
                "topic_ids": topic_ids,
                "source_candidate_count": len(candidates),
            }
        )
        for candidate in candidates:
            key = title_key(candidate)
            if not key:
                continue
            entry = grouped.setdefault(
                key,
                {
                    "canonical_title": candidate,
                    "raw_titles": set(),
                    "topic_ids": set(),
                    "report_names": set(),
                    "report_paths": set(),
                    "source_type_guess": guess_source_type(candidate),
                    "language_guess": guess_language(candidate),
                    "secret_like_detected": False,
                },
            )
            entry["raw_titles"].add(candidate)
            entry["topic_ids"].update(topic_ids)
            entry["report_names"].add(report_path.name)
            entry["report_paths"].add(rel_path(report_path, root_path))
            if SECRET_RE.search(candidate):
                entry["secret_like_detected"] = True
                secret_like_sources.add(key)

    sorted_entries = sorted(grouped.values(), key=lambda item: item["canonical_title"].lower())
    sources: list[dict[str, Any]] = []
    for index, entry in enumerate(sorted_entries, start=1):
        canonical_title = entry["canonical_title"]
        sources.append(
            {
                "source_id": f"rag004-source-{index:03d}",
                "stable_key": stable_hash(title_key(canonical_title)),
                "canonical_title": canonical_title,
                "raw_titles": sorted(entry["raw_titles"]),
                "topic_ids": sorted(entry["topic_ids"]),
                "topic_labels": [TOPIC_LABELS.get(topic_id, topic_id) for topic_id in sorted(entry["topic_ids"])],
                "report_names": sorted(entry["report_names"]),
                "report_paths": sorted(entry["report_paths"]),
                "source_type_guess": entry["source_type_guess"],
                "language_guess": entry["language_guess"],
                "source_type": "needs_review",
                "language": entry["language_guess"],
                "creator_or_author": "",
                "url": "",
                "publisher_or_channel": "",
                "publication_date": "",
                "rights_status": "needs_review",
                "metadata_status": "needs_human_review",
                "notebooklm_status": "imported_report_reference",
                "use_status": "candidate",
                "raw_source_text_stored": False,
                "secret_like_detected": entry["secret_like_detected"],
                "review_notes": "Fill URL/author/channel/source type/rights metadata before chunk import.",
            }
        )

    topic_to_source_ids: dict[str, list[str]] = defaultdict(list)
    for source in sources:
        for topic_id in source["topic_ids"]:
            topic_to_source_ids[topic_id].append(source["source_id"])

    sources_without_topics = [source["source_id"] for source in sources if not source["topic_ids"]]
    missing_review_metadata = [
        source["source_id"]
        for source in sources
        if not source["url"] or source["source_type"] == "needs_review" or source["rights_status"] == "needs_review"
    ]
    summary = {
        "report_count": len(reports_scanned),
        "source_count": len(sources),
        "source_id_mapping_review_required": True,
        "sources_missing_topic_count": len(sources_without_topics),
        "sources_missing_review_metadata_count": len(missing_review_metadata),
        "secret_like_source_count": len(secret_like_sources),
        "runtime_retrieval_enabled": False,
        "chunk_import_enabled": False,
        "external_provider_calls_made": False,
        "notebooklm_api_used": False,
        "raw_source_text_stored": False,
        "private_customer_data_used": False,
    }
    return {
        "manifest_id": RAG_SOURCE_MANIFEST_ID,
        "imports_dir": rel_path(imports_path, root_path),
        "summary": summary,
        "source_manifest": {
            "manifest_id": RAG_SOURCE_MANIFEST_ID,
            "version": 1,
            "workflow_role": "source-title normalization review, not runtime retrieval",
            "source_policy": {
                "store_metadata_only": True,
                "store_raw_source_text": False,
                "allow_private_customer_data": False,
                "allow_unsourced_chunks": False,
                "require_human_metadata_review": True,
            },
            "sources": sources,
            "topic_to_source_ids": dict(sorted((topic, sorted(ids)) for topic, ids in topic_to_source_ids.items())),
        },
        "reports_scanned": reports_scanned,
        "review_queues": {
            "sources_without_topics": sources_without_topics,
            "sources_missing_review_metadata": missing_review_metadata,
            "secret_like_sources": sorted(secret_like_sources),
        },
        "boundaries": {
            "runtime_retrieval_enabled": False,
            "chunk_import_enabled": False,
            "notebooklm_api_used": False,
            "external_provider_calls_made": False,
            "private_customer_data_allowed": False,
            "raw_source_text_import_allowed": False,
        },
    }


def render_manifest_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    sources = payload["source_manifest"]["sources"]
    lines = [
        "# RAG-004 Source Manifest Normalization",
        "",
        "This report converts source-title references from NotebookLM report artifacts into stable local source-ID candidates.",
        "",
        "Runtime retrieval remains disabled. RAG-004 does not import chunks, call NotebookLM, call providers, or promote any sales knowledge automatically.",
        "",
        "## Summary",
        "",
        f"- Imports folder: `{payload['imports_dir']}`",
        f"- Reports scanned: `{summary['report_count']}`",
        f"- Source candidates: `{summary['source_count']}`",
        f"- Source-ID mapping review required: `{summary['source_id_mapping_review_required']}`",
        f"- Sources missing review metadata: `{summary['sources_missing_review_metadata_count']}`",
        f"- Sources without topics: `{summary['sources_missing_topic_count']}`",
        f"- Secret-like source titles: `{summary['secret_like_source_count']}`",
        f"- Runtime retrieval enabled: `{summary['runtime_retrieval_enabled']}`",
        f"- Chunk import enabled: `{summary['chunk_import_enabled']}`",
        "",
        "## Source Candidates",
        "",
        "| Source ID | Title | Topics | Type Guess | Language | Review Status |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for source in sources:
        topics = ", ".join(source["topic_ids"]) or "needs_topic_review"
        title = source["canonical_title"].replace("|", "/")
        lines.append(
            f"| `{source['source_id']}` | {title} | {topics} | {source['source_type_guess']} | "
            f"{source['language_guess']} | {source['metadata_status']} |"
        )
    lines.extend(
        [
            "",
            "## Human Review Needed",
            "",
            "- Fill URL, author/channel, source type, language, rights status, and citation metadata where available.",
            "- Merge any duplicate titles that the heuristic did not recognize.",
            "- Delete any rows that are not real sources.",
            "- Keep source excerpts out of the manifest; this file is metadata-only.",
            "- Use reviewed source IDs in the later chunk-normalization checkpoint.",
            "",
            "## Boundaries",
            "",
            "- No private/customer data is allowed in this manifest.",
            "- No raw source text is stored.",
            "- No NotebookLM API or provider call is made.",
            "- No runtime retrieval or chunk import is enabled.",
            "",
        ]
    )
    return "\n".join(lines)
