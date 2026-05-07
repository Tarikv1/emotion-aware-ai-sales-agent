from __future__ import annotations

from copy import deepcopy
from typing import Any

from rag_knowledge_base import (
    build_source_manifest_template,
    get_topic_taxonomy,
    validate_notebooklm_chunks,
)


RAG_AUTOMATION_ID = "RAG-002-notebooklm-extraction-automation-bridge"
DEFAULT_PROMPT_CHAR_LIMIT = 4500
DEFAULT_CHAT_CUSTOMIZATION_CHAR_LIMIT = 10000
DEFAULT_MIN_CHUNKS_PER_TOPIC = 8
PROMPT_TYPES = ("report_artifact", "primary_report", "gap_check")


def make_issue(code: str, message: str, path: str = "") -> dict[str, str]:
    return {"code": code, "message": message, "path": path}


def topic_by_id() -> dict[str, dict[str, Any]]:
    return {topic["topic_id"]: topic for topic in get_topic_taxonomy()}


def sources_for_topic(manifest: dict[str, Any], topic_id: str) -> list[dict[str, Any]]:
    return [
        source
        for source in manifest.get("sources", [])
        if topic_id in source.get("topic_ids", [])
    ]


def compact_source_lines(sources: list[dict[str, Any]], max_chars: int = 1100) -> str:
    lines: list[str] = []
    used = 0
    omitted = 0
    for source in sources:
        source_id = str(source.get("source_id", "")).strip()
        title = str(source.get("title", "")).strip()[:90]
        source_type = str(source.get("source_type", "")).strip()
        language = str(source.get("language", "")).strip()
        line = f"- {source_id} | {title} | {source_type} | {language}"
        if used + len(line) + 1 > max_chars:
            omitted += 1
            continue
        lines.append(line)
        used += len(line) + 1
    if omitted:
        lines.append(f"- {omitted} additional source metadata row(s) omitted from prompt to stay inside the character limit.")
    return "\n".join(lines) if lines else "- No source metadata rows are available. Stop and report missing sources."


def json_contract(topic_id: str, min_chunks_per_topic: int) -> str:
    return (
        "{"
        f'"topic_id":"{topic_id}",'
        '"completion_status":"complete|partial|insufficient_source_material",'
        '"coverage_checklist":{'
        '"all_selected_sources_reviewed":true,'
        '"small_sample_batch":false,'
        '"no_more_distinct_items_found":true,'
        '"end_marker":"END: COMPLETE|NEED_CONTINUATION"'
        "},"
        '"tailored_report":{'
        '"source_coverage":"short source-by-source coverage note",'
        '"key_patterns":"complete non-summary report of reusable patterns",'
        '"agent_implications":"how this should improve sales reasoning, wording, emotion, or voice",'
        '"guardrails":"when not to use these ideas"'
        "},"
        '"chunks":[{'
        '"chunk_id":"stable-topic-slug-001",'
        '"topic_ids":["topic_id"],'
        '"source_ids":["source_id_from_manifest"],'
        '"language":"en|de|mixed",'
        '"sales_stage":["opening|relevance-check|objection|qualification|closing|handoff|voice-delivery"],'
        '"principle":"one reusable idea",'
        '"application":"when the sales agent should use it",'
        '"when_not_to_use":"clear boundary",'
        '"example_phrases":{"en":"short optional phrase","de":"short optional phrase"},'
        '"emotional_cues":["cue"],'
        '"compliance_notes":"risk notes",'
        '"evidence_type":"youtube|website|book|paper|mixed|synthetic_schema_demo",'
        '"confidence":"low|medium|high",'
        '"citation_note":"source title/time/page/section",'
        '"source_excerpt":"optional <=60 words"'
        "}]"
        "}"
        f" Need at least {min_chunks_per_topic} chunks when the source material supports it, but do not cap the extraction there."
    )


def build_chat_customization(
    *,
    chat_customization_char_limit: int = DEFAULT_CHAT_CUSTOMIZATION_CHAR_LIMIT,
) -> dict[str, Any]:
    text = """Role: You are a rigorous sales-research extraction assistant for the Emotion Aware AI Sales Agent thesis/product project.

Goal: turn the selected NotebookLM sources into complete, source-grounded, practical sales-agent knowledge. Always prefer exhaustive coverage over short summaries.

Choose response length: Longer.

Output behavior:
- First produce a readable tailored report with clear headings, bullets, tables when useful, and concrete agent implications.
- Then produce a machine-readable RAG JSON object when the prompt asks for it.
- Do not collapse the tailored report into short JSON strings.
- Do not give a small sample batch unless the prompt explicitly asks for a sample.
- Review all selected sources for the requested topic before claiming completion.
- If output limits stop you, write NEED_CONTINUATION instead of pretending the extraction is complete.

Extraction standards:
- Separate reusable sales principles, phrase patterns, emotional cues, voice/prosody implications, compliance/ethical guardrails, and when-not-to-use boundaries.
- Preserve source traceability with source titles, sections, timestamps, page notes, or citation notes.
- Merge duplicates, but do not omit distinct ideas.
- Keep claims conservative and source-grounded.
- Do not copy long passages, full transcripts, book chapters, private data, API keys, or unsourced claims.

Completion standard:
- Use END: COMPLETE only after all selected sources were reviewed and no more distinct useful items remain.
- If the source material is too thin for the requested minimum, say insufficient_source_material and explain why."""
    fitted = fit_prompt(text, chat_customization_char_limit)
    return {
        "title": "NotebookLM Configure Chat custom instructions",
        "char_limit": chat_customization_char_limit,
        "char_count": len(fitted),
        "text": fitted,
        "notebooklm_response_length": "Longer",
    }


def fit_prompt(text: str, prompt_char_limit: int) -> str:
    if len(text) <= prompt_char_limit:
        return text
    # Keep the instructions intact and trim only excess whitespace before failing.
    compact = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    if len(compact) <= prompt_char_limit:
        return compact
    raise ValueError(f"Prompt exceeds character limit: {len(compact)} > {prompt_char_limit}")


def build_primary_prompt(
    topic: dict[str, Any],
    sources: list[dict[str, Any]],
    prompt_char_limit: int,
    min_chunks_per_topic: int,
) -> dict[str, Any]:
    topic_id = topic["topic_id"]
    source_lines = compact_source_lines(sources)
    text = f"""Use the Configure Chat custom instructions for report style and coverage discipline.
NotebookLM is an extraction helper, not permanent product memory.

Topic: `{topic_id}` - {topic['label']}
Selected source metadata:
{source_lines}

Create a complete tailored extraction. This is not a summary.
Do not give me a small sample batch. Review all selected NotebookLM sources for this topic and extract every distinct reusable idea that can improve sales reasoning, ethical persuasion, objection handling, emotion adaptation, active listening, English/German phrasing, or voice/prosody.

Merge duplicates, but do not omit a distinct tactic, warning, emotion cue, phrase pattern, dataset point, or when-not-to-use boundary. Keep claims conservative and source-grounded. Do not copy long passages, full transcripts, book chapters, private data, API keys, or unsourced claims.

Return two sections:

PART A - TAILORED REPORT
Write a readable report with these headings: Source coverage; Complete reusable patterns; AI sales-agent implications; Voice/prosody implications; Ethical/compliance guardrails; Implementation candidates; Missing or weak evidence. Use enough detail that I do not need repeated small follow-up batches.

PART B - RAG JSON
Return one JSON object, no markdown fences:
{json_contract(topic_id, min_chunks_per_topic)}

Completion rule: use `"completion_status":"complete"` only if all selected sources were reviewed, `coverage_checklist.small_sample_batch=false`, no more distinct items remain, and `coverage_checklist.end_marker="END: COMPLETE"`. If output limits prevent completion, set `"partial"` and `"NEED_CONTINUATION"`."""
    return {
        "prompt_type": "primary_report",
        "title": f"{topic['label']} exhaustive report and chunks",
        "char_limit": prompt_char_limit,
        "char_count": len(fit_prompt(text, prompt_char_limit)),
        "text": fit_prompt(text, prompt_char_limit),
    }


def build_report_artifact_prompt(
    topic: dict[str, Any],
    sources: list[dict[str, Any]],
    prompt_char_limit: int,
    min_chunks_per_topic: int,
) -> dict[str, Any]:
    topic_id = topic["topic_id"]
    source_lines = compact_source_lines(sources)
    text = f"""Use NotebookLM Reports / Create report for this task, not a normal chat reply.
NotebookLM is an extraction helper, not permanent product memory.

Create a NotebookLM report file for:
Topic: `{topic_id}` - {topic['label']}

Selected source metadata:
{source_lines}

Do not answer only in chat. Create a report file/document that can be exported or copied after generation.

Report title:
Emotion Aware AI Sales Agent - {topic['label']} Source Extraction Report

Report requirements:
- Make this a complete tailored report, not a short summary.
- Review all selected sources for this topic before claiming completion.
- Do not give me a small sample batch.
- Extract every distinct reusable idea that can improve sales reasoning, ethical persuasion, objection handling, emotion adaptation, active listening, English/German phrasing, or voice/prosody.
- Merge duplicates, but do not omit distinct tactics, warnings, emotion cues, phrase patterns, dataset points, or when-not-to-use boundaries.
- Keep claims conservative and source-grounded.
- Do not copy long passages, full transcripts, book chapters, private data, API keys, or unsourced claims.

Required report sections:
1. Source coverage table
2. Executive synthesis for the AI sales-agent product
3. Complete reusable sales patterns
4. Phrase and dialogue patterns
5. Emotion/adaptation cues
6. Voice/prosody and delivery implications
7. Ethical/compliance guardrails
8. Campaign configuration implications
9. RAG-ready extraction appendix with at least {min_chunks_per_topic} distinct chunk candidates if the source material supports it
10. Missing or weak evidence
11. Completion statement: END: COMPLETE or NEED_CONTINUATION

The RAG-ready extraction appendix must include: stable chunk id, source title/id, topic id `{topic_id}`, language, sales stage, principle, application, when not to use, example phrase if available, emotional cues, compliance notes, evidence type, confidence, citation note, and optional short source excerpt <=60 words.

Export or copy the completed report file after NotebookLM creates it. If output limits prevent completion, mark NEED_CONTINUATION and do not pretend the report is complete."""
    fitted = fit_prompt(text, prompt_char_limit)
    return {
        "prompt_type": "report_artifact",
        "title": f"{topic['label']} NotebookLM report file prompt",
        "char_limit": prompt_char_limit,
        "char_count": len(fitted),
        "text": fitted,
    }


def build_gap_check_prompt(
    topic: dict[str, Any],
    sources: list[dict[str, Any]],
    prompt_char_limit: int,
    min_chunks_per_topic: int,
) -> dict[str, Any]:
    topic_id = topic["topic_id"]
    source_lines = compact_source_lines(sources, max_chars=900)
    text = f"""Coverage gap check for Emotion Aware AI Sales Agent RAG extraction.
Topic: `{topic_id}` - {topic['label']}
Source metadata:
{source_lines}

Look again across all selected NotebookLM sources for this topic and find missing distinct items from the previous answer. Do not repeat existing chunk_ids or duplicated ideas. Focus on sales tactics, objections, discovery, emotional cues, voice/prosody, English/German phrasing, guardrails, datasets, and when-not-to-use boundaries that were not captured.

Return exactly one JSON object using the same schema as before. If there are missing items, include only the missing chunks and set `"completion_status":"partial"` with `"NEED_CONTINUATION"` unless you finish the full gap check. If no missing items remain, return `"chunks":[]`, `"completion_status":"complete"`, `coverage_checklist.small_sample_batch=false`, and `coverage_checklist.end_marker="END: COMPLETE"`.

Minimum coverage reminder: the main extraction should have at least {min_chunks_per_topic} chunks when the source material supports it. If fewer are valid, explain why with `"completion_status":"insufficient_source_material"`."""
    return {
        "prompt_type": "gap_check",
        "title": f"{topic['label']} coverage gap check",
        "char_limit": prompt_char_limit,
        "char_count": len(fit_prompt(text, prompt_char_limit)),
        "text": fit_prompt(text, prompt_char_limit),
    }


def build_notebooklm_prompt_pack(
    manifest: dict[str, Any] | None = None,
    *,
    prompt_char_limit: int = DEFAULT_PROMPT_CHAR_LIMIT,
    chat_customization_char_limit: int = DEFAULT_CHAT_CUSTOMIZATION_CHAR_LIMIT,
    min_chunks_per_topic: int = DEFAULT_MIN_CHUNKS_PER_TOPIC,
) -> dict[str, Any]:
    source_manifest = deepcopy(manifest) if manifest else build_source_manifest_template()
    topics = source_manifest.get("topics") or get_topic_taxonomy()
    topic_entries: list[dict[str, Any]] = []
    for topic in topics:
        topic_id = topic["topic_id"]
        sources = sources_for_topic(source_manifest, topic_id)
        primary = build_primary_prompt(topic, sources, prompt_char_limit, min_chunks_per_topic)
        report_artifact = build_report_artifact_prompt(topic, sources, prompt_char_limit, min_chunks_per_topic)
        gap_check = build_gap_check_prompt(topic, sources, prompt_char_limit, min_chunks_per_topic)
        topic_entries.append(
            {
                "topic_id": topic_id,
                "label": topic["label"],
                "source_ids": [source.get("source_id", "") for source in sources],
                "prompts": {
                    "report_artifact": report_artifact,
                    "primary_report": primary,
                    "gap_check": gap_check,
                },
            }
        )
    return {
        "rag_automation_id": RAG_AUTOMATION_ID,
        "workflow_role": "NotebookLM UI extraction automation bridge",
        "prompt_char_limit": prompt_char_limit,
        "chat_customization_char_limit": chat_customization_char_limit,
        "min_chunks_per_topic": min_chunks_per_topic,
        "chat_customization": build_chat_customization(chat_customization_char_limit=chat_customization_char_limit),
        "manual_notebooklm_ui_required": True,
        "notebooklm_api_used": False,
        "external_provider_calls_made": False,
        "raw_source_text_stored": False,
        "customer_private_data_used": False,
        "topics": topic_entries,
    }


def validate_prompt_pack(prompt_pack: dict[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    prompt_char_limit = int(prompt_pack.get("prompt_char_limit", DEFAULT_PROMPT_CHAR_LIMIT))
    chat_customization = prompt_pack.get("chat_customization") or {}
    chat_customization_char_limit = int(prompt_pack.get("chat_customization_char_limit", DEFAULT_CHAT_CUSTOMIZATION_CHAR_LIMIT))
    chat_customization_text = str(chat_customization.get("text", ""))
    chat_customization_within_limit = len(chat_customization_text) <= chat_customization_char_limit
    if not chat_customization_text:
        issues.append(make_issue("missing_chat_customization", "Configure Chat custom instructions are missing.", "chat_customization.text"))
    if not chat_customization_within_limit:
        issues.append(make_issue("chat_customization_over_limit", f"Configure Chat instructions are {len(chat_customization_text)} chars.", "chat_customization.text"))
    if "Do not collapse the tailored report into short JSON strings" not in chat_customization_text:
        issues.append(make_issue("chat_customization_missing_report_guard", "Configure Chat instructions do not protect report detail.", "chat_customization.text"))
    prompt_count = 0
    all_prompts_within_limit = True
    all_prompts_have_completion_marker = True
    all_primary_prompts_are_exhaustive = True
    primary_prompts_include_readable_report = True
    primary_prompts_include_json_block = True
    all_topics_have_report_artifact_prompt = True
    report_artifact_workflow_enabled = True
    for topic_index, topic_entry in enumerate(prompt_pack.get("topics", [])):
        prompts = topic_entry.get("prompts", {})
        for prompt_type in PROMPT_TYPES:
            prompt_count += 1
            prompt = prompts.get(prompt_type) or {}
            text = str(prompt.get("text", ""))
            path = f"topics[{topic_index}].prompts.{prompt_type}"
            if len(text) > prompt_char_limit:
                all_prompts_within_limit = False
                issues.append(make_issue("prompt_over_char_limit", f"{prompt_type} is {len(text)} chars.", path))
            if "END: COMPLETE" not in text or "NEED_CONTINUATION" not in text:
                all_prompts_have_completion_marker = False
                issues.append(make_issue("missing_completion_marker", f"{prompt_type} is missing completion markers.", path))
            if prompt_type == "report_artifact":
                required = ["Create a NotebookLM report file", "Do not answer only in chat", "Export or copy the completed report file", "RAG-ready extraction appendix"]
                missing = [phrase for phrase in required if phrase not in text]
                if missing:
                    all_topics_have_report_artifact_prompt = False
                    report_artifact_workflow_enabled = False
                    issues.append(make_issue("report_artifact_prompt_incomplete", f"Missing: {', '.join(missing)}", path))
            if prompt_type == "primary_report":
                required = ["Do not give me a small sample batch", "tailored extraction report", "coverage_checklist"]
                # Accept the newer "complete tailored extraction" phrasing while retaining the exhaustive intent.
                if "tailored extraction report" not in text and "complete tailored extraction" in text:
                    required.remove("tailored extraction report")
                missing = [phrase for phrase in required if phrase not in text]
                if missing:
                    all_primary_prompts_are_exhaustive = False
                    issues.append(make_issue("primary_prompt_not_exhaustive", f"Missing: {', '.join(missing)}", path))
                if "PART A - TAILORED REPORT" not in text:
                    primary_prompts_include_readable_report = False
                    issues.append(make_issue("primary_prompt_missing_readable_report", "Primary prompt does not require a readable report section.", path))
                if "PART B - RAG JSON" not in text:
                    primary_prompts_include_json_block = False
                    issues.append(make_issue("primary_prompt_missing_json_block", "Primary prompt does not require a RAG JSON section.", path))
    topic_count = len(prompt_pack.get("topics", []))
    passed = (
        not issues
        and topic_count == len(get_topic_taxonomy())
        and all_prompts_within_limit
        and all_prompts_have_completion_marker
        and all_primary_prompts_are_exhaustive
        and primary_prompts_include_readable_report
        and primary_prompts_include_json_block
        and chat_customization_within_limit
        and all_topics_have_report_artifact_prompt
        and report_artifact_workflow_enabled
    )
    return {
        "passed": passed,
        "topic_count": topic_count,
        "prompt_count": prompt_count,
        "prompt_char_limit": prompt_char_limit,
        "chat_customization_char_limit": chat_customization_char_limit,
        "chat_customization_within_limit": chat_customization_within_limit,
        "all_topics_have_report_artifact_prompt": all_topics_have_report_artifact_prompt,
        "report_artifact_workflow_enabled": report_artifact_workflow_enabled,
        "all_prompts_within_limit": all_prompts_within_limit,
        "all_prompts_have_completion_marker": all_prompts_have_completion_marker,
        "all_primary_prompts_are_exhaustive": all_primary_prompts_are_exhaustive,
        "primary_prompts_include_readable_report": primary_prompts_include_readable_report,
        "primary_prompts_include_json_block": primary_prompts_include_json_block,
        "manual_notebooklm_ui_required": bool(prompt_pack.get("manual_notebooklm_ui_required", True)),
        "notebooklm_api_used": bool(prompt_pack.get("notebooklm_api_used", False)),
        "issues": issues,
    }


def validate_extraction_output(
    extraction_output: dict[str, Any],
    manifest: dict[str, Any],
    *,
    topic_id: str,
    min_chunks_per_topic: int = DEFAULT_MIN_CHUNKS_PER_TOPIC,
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if extraction_output.get("topic_id") != topic_id:
        issues.append(make_issue("topic_id_mismatch", f"Expected topic_id {topic_id}.", "topic_id"))

    completion_status = extraction_output.get("completion_status")
    coverage = extraction_output.get("coverage_checklist") or {}
    chunks = extraction_output.get("chunks") or []
    insufficient_source_material = completion_status == "insufficient_source_material"

    if completion_status != "complete" and not insufficient_source_material:
        issues.append(make_issue("completion_status_not_complete", "Extraction must be complete before import.", "completion_status"))
    if coverage.get("all_selected_sources_reviewed") is not True and not insufficient_source_material:
        issues.append(make_issue("sources_not_fully_reviewed", "Coverage checklist does not confirm all sources were reviewed.", "coverage_checklist.all_selected_sources_reviewed"))
    if coverage.get("small_sample_batch") is not False:
        issues.append(make_issue("small_sample_batch_detected", "NotebookLM output looks like a sample batch.", "coverage_checklist.small_sample_batch"))
    if coverage.get("no_more_distinct_items_found") is not True and not insufficient_source_material:
        issues.append(make_issue("distinct_items_may_remain", "Coverage checklist says distinct items may remain.", "coverage_checklist.no_more_distinct_items_found"))
    if coverage.get("end_marker") != "END: COMPLETE" and not insufficient_source_material:
        issues.append(make_issue("missing_complete_end_marker", "Output must end with END: COMPLETE before import.", "coverage_checklist.end_marker"))
    if len(chunks) < min_chunks_per_topic and not insufficient_source_material:
        issues.append(make_issue("too_few_chunks_for_topic", f"Expected at least {min_chunks_per_topic} chunks or an insufficient_source_material status.", "chunks"))

    chunk_report = validate_notebooklm_chunks(chunks, manifest)
    for issue in chunk_report.get("issues", []):
        issues.append(make_issue(f"chunk_{issue.get('code', 'invalid')}", issue.get("message", "Invalid chunk."), issue.get("path", "")))
    for index, chunk in enumerate(chunks):
        if topic_id not in chunk.get("topic_ids", []):
            issues.append(make_issue("chunk_missing_requested_topic", f"Chunk {chunk.get('chunk_id', index)} does not include {topic_id}.", f"chunks[{index}].topic_ids"))

    coverage_complete = (
        completion_status == "complete"
        and coverage.get("all_selected_sources_reviewed") is True
        and coverage.get("small_sample_batch") is False
        and coverage.get("no_more_distinct_items_found") is True
        and coverage.get("end_marker") == "END: COMPLETE"
    )
    return {
        "passed": not issues,
        "topic_id": topic_id,
        "chunk_count": len(chunks),
        "min_chunks_per_topic": min_chunks_per_topic,
        "coverage_complete": coverage_complete,
        "small_sample_batch_detected": coverage.get("small_sample_batch") is not False,
        "chunk_validation_passed": chunk_report.get("passed", False),
        "issues": issues,
    }
