Use the Configure Chat custom instructions for report style and coverage discipline.
NotebookLM is an extraction helper, not permanent product memory.

Topic: `negotiation_german_english_sales_calls_telefonakquise` - Negotiation, English/German sales calls, and Telefonakquise
Selected source metadata:
- rag001-slot-07-negotiation_german_english_sales_calls_telefonakquise | Negotiation, English/German sales calls, and Telefonakquise source slot | source_slot | mixed

Create a complete tailored extraction. This is not a summary.
Do not give me a small sample batch. Review all selected NotebookLM sources for this topic and extract every distinct reusable idea that can improve sales reasoning, ethical persuasion, objection handling, emotion adaptation, active listening, English/German phrasing, or voice/prosody.

Merge duplicates, but do not omit a distinct tactic, warning, emotion cue, phrase pattern, dataset point, or when-not-to-use boundary. Keep claims conservative and source-grounded. Do not copy long passages, full transcripts, book chapters, private data, API keys, or unsourced claims.

Return two sections:

PART A - TAILORED REPORT
Write a readable report with these headings: Source coverage; Complete reusable patterns; AI sales-agent implications; Voice/prosody implications; Ethical/compliance guardrails; Implementation candidates; Missing or weak evidence. Use enough detail that I do not need repeated small follow-up batches.

PART B - RAG JSON
Return one JSON object, no markdown fences:
{"topic_id":"negotiation_german_english_sales_calls_telefonakquise","completion_status":"complete|partial|insufficient_source_material","coverage_checklist":{"all_selected_sources_reviewed":true,"small_sample_batch":false,"no_more_distinct_items_found":true,"end_marker":"END: COMPLETE|NEED_CONTINUATION"},"tailored_report":{"source_coverage":"short source-by-source coverage note","key_patterns":"complete non-summary report of reusable patterns","agent_implications":"how this should improve sales reasoning, wording, emotion, or voice","guardrails":"when not to use these ideas"},"chunks":[{"chunk_id":"stable-topic-slug-001","topic_ids":["topic_id"],"source_ids":["source_id_from_manifest"],"language":"en|de|mixed","sales_stage":["opening|relevance-check|objection|qualification|closing|handoff|voice-delivery"],"principle":"one reusable idea","application":"when the sales agent should use it","when_not_to_use":"clear boundary","example_phrases":{"en":"short optional phrase","de":"short optional phrase"},"emotional_cues":["cue"],"compliance_notes":"risk notes","evidence_type":"youtube|website|book|paper|mixed|synthetic_schema_demo","confidence":"low|medium|high","citation_note":"source title/time/page/section","source_excerpt":"optional <=60 words"}]} Need at least 8 chunks when the source material supports it, but do not cap the extraction there.

Completion rule: use `"completion_status":"complete"` only if all selected sources were reviewed, `coverage_checklist.small_sample_batch=false`, no more distinct items remain, and `coverage_checklist.end_marker="END: COMPLETE"`. If output limits prevent completion, set `"partial"` and `"NEED_CONTINUATION"`.