from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from runtime.retrieval.knowledge_base import get_topic_taxonomy


RAG_REPORT_IMPORT_READINESS_ID = "RAG-003-report-import-readiness"

SECRET_RE = re.compile(
    r"sk-[A-Za-z0-9_-]{20,}|sk_car_[A-Za-z0-9_-]{12,}|xi-api-key\s*[:=]\s*[A-Za-z0-9]|"
    r"ELEVENLABS_API_KEY|OPENAI_API_KEY|CARTESIA_API_KEY|AIza[0-9A-Za-z_-]{20,}",
    re.IGNORECASE,
)

SOURCE_COVERAGE_RE = re.compile(
    r"source\s+coverage|sources\s+reviewed|source-by-source|coverage\s+table|coverage\s+matrix",
    re.IGNORECASE,
)
RAG_APPENDIX_RE = re.compile(
    r"rag[-\s]?ready|chunk\s+candidates?|extraction\s+appendix|stable\s+chunk\s+id|chunk_id|chunk\\_id",
    re.IGNORECASE,
)
GAP_OR_CONTINUATION_RE = re.compile(
    r"gap[-\s]?check|coverage\s+gap|additional\s+gaps|coverage_checklist|coverage\\_checklist|"
    r"no_more_distinct_items_found|no\\_more\\_distinct\\_items\\_found",
    re.IGNORECASE,
)
QUOTE_REVIEW_RE = re.compile(
    r"source_excerpt|source\\_excerpt|verbatim|direct\s+quote|transcript|quoted\s+passage",
    re.IGNORECASE,
)

TOPIC_HINTS = {
    "cold_calling": ["cold calling", "cold_calling", "kaltakquise"],
    "closing_techniques": ["closing techniques", "closing_techniques", "closing"],
    "objection_handling": ["objection handling", "objection_handling", "einwand"],
    "consultative_selling_discovery": [
        "consultative selling",
        "consultative_selling_discovery",
        "discovery",
    ],
    "emotional_intelligence": ["emotional intelligence", "emotional_intelligence"],
    "active_listening_human_like_sales_communication": [
        "active listening",
        "human-like sales communication",
        "active_listening_human_like_sales_communication",
    ],
    "negotiation_german_english_sales_calls_telefonakquise": [
        "negotiation_german_english_sales_calls_telefonakquise",
        "telefonakquise",
        "german sales",
        "english sales",
    ],
    "ethical_persuasion_persuasive_dialogue": [
        "ethical_persuasion_persuasive_dialogue",
        "ethical persuasion",
        "persuasive dialogue",
        "persuasion",
    ],
    "speech_tone_prosody_human_like_voice_behavior": [
        "speech_tone_prosody_human_like_voice_behavior",
        "speech, tone, prosody",
        "voice and behavioral logic",
        "prosody",
        "tts",
    ],
    "emotion_recognition_speech_emotion_persuasion_datasets": [
        "emotion_recognition_speech_emotion_persuasion_datasets",
        "emotion recognition",
        "speech emotion",
        "persuasion datasets",
    ],
}


def normalize_report_text(text: str) -> str:
    return text.replace("\\_", "_").replace("\\-", "-")


def expected_topic_ids() -> list[str]:
    return [topic["topic_id"] for topic in get_topic_taxonomy()]


def rel_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def markdown_reports(import_dir: Path) -> list[Path]:
    if not import_dir.exists():
        return []
    return sorted(
        path
        for path in import_dir.glob("*.md")
        if path.is_file() and path.name.lower() != "readme.md"
    )


def heading_count(text: str) -> int:
    return len(re.findall(r"(?m)^#{1,6}\s+", text))


def first_heading(text: str) -> str:
    match = re.search(r"(?m)^#{1,6}\s+(.+)$", text)
    return match.group(1).strip() if match else ""


def explicit_topic_ids(normalized_text: str) -> list[str]:
    known = set(expected_topic_ids())
    found = []
    topic_id_matches = re.findall(
        r"(?i)(?:\"?topic_id\"?|\"?topic\"?|topic\s+id)\s*[:=,]\s*\"?([a-z0-9_]+)",
        normalized_text,
    )
    for topic_id in topic_id_matches:
        if topic_id in known:
            found.append(topic_id)
    return sorted(set(found))


def infer_topic_ids(path: Path, normalized_text: str) -> list[str]:
    explicit = explicit_topic_ids(normalized_text)
    if explicit:
        return explicit
    haystack = f"{path.name}\n{first_heading(normalized_text)}\n{normalized_text[:1200]}".lower()
    matched = []
    for topic_id, hints in TOPIC_HINTS.items():
        if any(hint.lower() in haystack for hint in hints):
            matched.append(topic_id)
    return matched


def count_after_first_complete_marker(normalized_text: str) -> int:
    marker = "END: COMPLETE"
    index = normalized_text.find(marker)
    if index == -1:
        return 0
    return len(normalized_text[index + len(marker) :].strip())


def appended_chat_output_detected(normalized_text: str) -> bool:
    marker = "END: COMPLETE"
    index = normalized_text.find(marker)
    if index == -1:
        return False
    tail = normalized_text[index + len(marker) :]
    return bool(
        len(tail.strip()) > 200
        and re.search(r"coverage_checklist|chunk_id|completion_status|topic_id", tail, re.IGNORECASE)
    )


def duplicate_structure_detected(normalized_text: str) -> bool:
    source_coverage_count = len(re.findall(r"(?im)^#{1,6}\s+.*source\s+coverage", normalized_text))
    rag_appendix_count = len(
        re.findall(r"(?im)^#{1,6}\s+.*(?:rag[-\s]?ready|extraction\s+appendix)", normalized_text)
    )
    report_heading_count = len(re.findall(r"(?im)^#{1,6}\s+.*source\s+extraction\s+report", normalized_text))
    return source_coverage_count > 1 or rag_appendix_count > 1 or report_heading_count > 1


def uses_stable_source_ids(normalized_text: str) -> bool:
    return bool(re.search(r"rag001-slot-\d{2}-[a-z0-9_]+", normalized_text))


def audit_report(path: Path, root: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    normalized = normalize_report_text(text)
    topic_ids = infer_topic_ids(path, normalized)
    flags: list[str] = []
    source_coverage_present = bool(SOURCE_COVERAGE_RE.search(normalized))
    rag_appendix_present = bool(RAG_APPENDIX_RE.search(normalized))
    complete_marker_present = "END: COMPLETE" in normalized
    need_continuation_present = "NEED_CONTINUATION" in normalized
    gap_or_continuation_present = bool(GAP_OR_CONTINUATION_RE.search(normalized))
    appended_output_present = appended_chat_output_detected(normalized)
    duplicate_structure_present = duplicate_structure_detected(normalized)
    source_id_mapping_required = not uses_stable_source_ids(normalized)
    quote_review_recommended = bool(QUOTE_REVIEW_RE.search(normalized))
    secret_like_detected = bool(SECRET_RE.search(normalized))

    if not topic_ids:
        flags.append("topic_mapping_required")
    if not complete_marker_present:
        flags.append("missing_complete_marker")
    if need_continuation_present:
        flags.append("needs_continuation")
    if not source_coverage_present:
        flags.append("missing_source_coverage_section")
    if not rag_appendix_present:
        flags.append("missing_rag_ready_appendix")
    if source_id_mapping_required:
        flags.append("source_id_mapping_required")
    if appended_output_present:
        flags.append("appended_chat_or_gap_output_detected")
    if duplicate_structure_present:
        flags.append("mixed_or_duplicate_report_structure")
    if quote_review_recommended:
        flags.append("quote_review_recommended")
    if secret_like_detected:
        flags.append("secret_like_text_detected")

    return {
        "path": rel_path(path, root),
        "name": path.name,
        "size_bytes": path.stat().st_size,
        "heading_count": heading_count(normalized),
        "first_heading": first_heading(normalized),
        "topic_ids": topic_ids,
        "complete_marker_present": complete_marker_present,
        "need_continuation_present": need_continuation_present,
        "source_coverage_present": source_coverage_present,
        "rag_appendix_present": rag_appendix_present,
        "gap_or_continuation_present": gap_or_continuation_present,
        "appended_chat_or_gap_output_detected": appended_output_present,
        "duplicate_structure_detected": duplicate_structure_present,
        "source_id_mapping_required": source_id_mapping_required,
        "quote_review_recommended": quote_review_recommended,
        "secret_like_detected": secret_like_detected,
        "chars_after_first_complete_marker": count_after_first_complete_marker(normalized),
        "review_flags": flags,
    }


def build_recommendations(summary: dict[str, Any]) -> list[str]:
    recommendations: list[str] = []
    if summary["missing_topic_ids"]:
        recommendations.append("Collect or map missing topic reports before any RAG promotion.")
    if summary["need_continuation_count"]:
        recommendations.append("Run NotebookLM gap checks for reports that still contain NEED_CONTINUATION.")
    if summary["source_id_mapping_required"]:
        recommendations.append("Create a real source manifest that maps NotebookLM source titles to stable source IDs before chunk import.")
    if summary["reports_with_appended_output"]:
        recommendations.append("Normalize pasted chat/gap-check continuations into appendices before chunk extraction.")
    if summary["reports_missing_source_coverage"]:
        recommendations.append("Ask NotebookLM to regenerate or patch reports missing source coverage evidence.")
    if summary["reports_missing_rag_appendix"]:
        recommendations.append("Ask NotebookLM to regenerate or patch reports missing RAG-ready chunk appendices.")
    if summary["reports_needing_quote_review"]:
        recommendations.append("Review source excerpts before committing or importing chunks to keep copyright exposure low.")
    if not recommendations:
        recommendations.append("Proceed to manual source-ID mapping and chunk-normalization design; do not enable runtime retrieval yet.")
    return recommendations


def summarize_reports(reports: list[dict[str, Any]]) -> dict[str, Any]:
    expected = expected_topic_ids()
    topic_to_reports: dict[str, list[str]] = defaultdict(list)
    for report in reports:
        for topic_id in report["topic_ids"]:
            if topic_id in expected:
                topic_to_reports[topic_id].append(report["name"])
    covered = sorted(topic_to_reports)
    missing = [topic_id for topic_id in expected if topic_id not in topic_to_reports]
    topic_counts = Counter(topic for report in reports for topic in report["topic_ids"] if topic in expected)
    duplicate_topics = sorted(topic_id for topic_id, count in topic_counts.items() if count > 1)
    reports_with_secret = [report["name"] for report in reports if report["secret_like_detected"]]
    reports_missing_source_coverage = [report["name"] for report in reports if not report["source_coverage_present"]]
    reports_missing_rag_appendix = [report["name"] for report in reports if not report["rag_appendix_present"]]
    reports_with_appended_output = [report["name"] for report in reports if report["appended_chat_or_gap_output_detected"]]
    reports_needing_quote_review = [report["name"] for report in reports if report["quote_review_recommended"]]
    source_id_mapping_required = any(report["source_id_mapping_required"] for report in reports)
    need_continuation_count = sum(1 for report in reports if report["need_continuation_present"])

    blocked = bool(missing or reports_with_secret or need_continuation_count)
    review_required = bool(
        blocked
        or source_id_mapping_required
        or reports_missing_source_coverage
        or reports_missing_rag_appendix
        or reports_with_appended_output
        or duplicate_topics
        or reports_needing_quote_review
    )
    import_readiness = "blocked" if blocked else "review_required" if review_required else "ready_for_manual_chunk_normalization"
    return {
        "expected_topic_count": len(expected),
        "report_count": len(reports),
        "covered_topic_count": len(covered),
        "covered_topic_ids": covered,
        "missing_topic_ids": missing,
        "duplicate_topic_ids": duplicate_topics,
        "topic_to_reports": dict(sorted(topic_to_reports.items())),
        "all_reports_have_complete_marker": all(report["complete_marker_present"] for report in reports) if reports else False,
        "all_reports_have_source_coverage": all(report["source_coverage_present"] for report in reports) if reports else False,
        "all_reports_have_rag_appendix": all(report["rag_appendix_present"] for report in reports) if reports else False,
        "need_continuation_count": need_continuation_count,
        "secret_like_report_count": len(reports_with_secret),
        "reports_with_secret_like_text": reports_with_secret,
        "reports_missing_source_coverage": reports_missing_source_coverage,
        "reports_missing_rag_appendix": reports_missing_rag_appendix,
        "reports_with_appended_output": reports_with_appended_output,
        "reports_needing_quote_review": reports_needing_quote_review,
        "source_id_mapping_required": source_id_mapping_required,
        "import_readiness": import_readiness,
        "runtime_retrieval_enabled": False,
        "safe_to_auto_promote": False,
        "external_provider_calls_made": False,
        "notebooklm_api_used": False,
        "raw_private_data_used": False,
    }


def audit_import_directory(import_dir: Path | str, *, root: Path | None = None) -> dict[str, Any]:
    root_path = root or Path(__file__).resolve().parents[1]
    imports_path = Path(import_dir)
    if not imports_path.is_absolute():
        imports_path = root_path / imports_path
    reports = [audit_report(path, root_path) for path in markdown_reports(imports_path)]
    summary = summarize_reports(reports)
    payload = {
        "audit_id": RAG_REPORT_IMPORT_READINESS_ID,
        "imports_dir": rel_path(imports_path, root_path),
        "summary": summary,
        "recommendations": build_recommendations(summary),
        "reports": reports,
        "boundaries": {
            "runtime_retrieval_enabled": False,
            "auto_promotion_allowed": False,
            "notebooklm_api_used": False,
            "external_provider_calls_made": False,
            "private_customer_data_allowed": False,
            "raw_source_text_import_allowed": False,
        },
    }
    return payload


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# RAG-003 Report Import Readiness",
        "",
        "This report audits NotebookLM report files that were manually exported or pasted into the RAG-002 imports folder.",
        "",
        "Runtime retrieval remains disabled. RAG-003 does not import chunks, call NotebookLM, call providers, or promote any sales knowledge automatically.",
        "",
        "## Summary",
        "",
        f"- Imports folder: `{payload['imports_dir']}`",
        f"- Reports scanned: `{summary['report_count']}`",
        f"- Topic coverage: `{summary['covered_topic_count']} / {summary['expected_topic_count']}`",
        f"- Import readiness: `{summary['import_readiness']}`",
        f"- Complete markers on all reports: `{summary['all_reports_have_complete_marker']}`",
        f"- Source coverage on all reports: `{summary['all_reports_have_source_coverage']}`",
        f"- RAG appendix on all reports: `{summary['all_reports_have_rag_appendix']}`",
        f"- Reports needing continuation: `{summary['need_continuation_count']}`",
        f"- Source-ID mapping required: `{summary['source_id_mapping_required']}`",
        f"- Safe to auto-promote: `{summary['safe_to_auto_promote']}`",
        "",
        "## Topic Coverage",
        "",
    ]
    if summary["missing_topic_ids"]:
        lines.append("Missing topics:")
        for topic_id in summary["missing_topic_ids"]:
            lines.append(f"- `{topic_id}`")
    else:
        lines.append("All expected topics are covered by at least one report.")
    lines.append("")
    for topic_id, report_names in summary["topic_to_reports"].items():
        joined = "; ".join(report_names)
        lines.append(f"- `{topic_id}`: {joined}")
    lines.extend(["", "## Report Flags", ""])
    for report in payload["reports"]:
        flags = ", ".join(f"`{flag}`" for flag in report["review_flags"]) if report["review_flags"] else "`none`"
        topics = ", ".join(f"`{topic}`" for topic in report["topic_ids"]) or "`unmapped`"
        lines.append(f"- `{report['name']}` -> topics {topics}; flags {flags}")
    lines.extend(["", "## Recommendations", ""])
    for recommendation in payload["recommendations"]:
        lines.append(f"- {recommendation}")
    lines.extend(
        [
            "",
            "## Boundaries",
            "",
            "- This checkpoint accepts NotebookLM report artifacts as raw research intake only.",
            "- Do not commit or promote source excerpts without quote/copyright review.",
            "- Do not use report text as runtime behavior until source IDs, chunk boundaries, and guardrails are normalized.",
            "- Runtime retrieval remains disabled until a later reviewed RAG checkpoint.",
            "",
        ]
    )
    return "\n".join(lines)
