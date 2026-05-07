Coverage gap check for Emotion Aware AI Sales Agent RAG extraction.
Topic: `emotion_recognition_speech_emotion_persuasion_datasets` - Emotion recognition, speech emotion datasets, and persuasion datasets
Source metadata:
- rag001-slot-10-emotion_recognition_speech_emotion_persuasion_datasets | Emotion recognition, speech emotion datasets, and persuasion datasets source slot | source_slot | mixed

Look again across all selected NotebookLM sources for this topic and find missing distinct items from the previous answer. Do not repeat existing chunk_ids or duplicated ideas. Focus on sales tactics, objections, discovery, emotional cues, voice/prosody, English/German phrasing, guardrails, datasets, and when-not-to-use boundaries that were not captured.

Return exactly one JSON object using the same schema as before. If there are missing items, include only the missing chunks and set `"completion_status":"partial"` with `"NEED_CONTINUATION"` unless you finish the full gap check. If no missing items remain, return `"chunks":[]`, `"completion_status":"complete"`, `coverage_checklist.small_sample_batch=false`, and `coverage_checklist.end_marker="END: COMPLETE"`.

Minimum coverage reminder: the main extraction should have at least 8 chunks when the source material supports it. If fewer are valid, explain why with `"completion_status":"insufficient_source_material"`.