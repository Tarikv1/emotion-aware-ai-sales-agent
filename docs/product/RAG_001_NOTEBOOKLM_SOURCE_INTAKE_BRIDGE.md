# RAG-001 NotebookLM Source Intake Bridge

RAG-001 creates the first local source-intake bridge for the sales knowledge base.

NotebookLM is treated as an extraction helper, not permanent product memory.

## Purpose

Tarik is collecting sources from YouTube videos, websites, books, PDFs, and datasets. The goal is to turn those sources into source-tracked, paraphrased RAG chunks for the reusable sales-agent core.

This checkpoint keeps the process organized:

```text
source metadata
  -> NotebookLM extraction prompt
  -> source-tracked JSON chunks
  -> local validation
  -> generated knowledge-base preview
```

Runtime retrieval is not enabled yet.

## Topic Taxonomy

RAG-001 uses the first 10 active source subjects:

1. `cold_calling`
2. `closing_techniques`
3. `objection_handling`
4. `consultative_selling_discovery`
5. `emotional_intelligence`
6. `active_listening_human_like_sales_communication`
7. `negotiation_german_english_sales_calls_telefonakquise`
8. `ethical_persuasion_persuasive_dialogue`
9. `speech_tone_prosody_human_like_voice_behavior`
10. `emotion_recognition_speech_emotion_persuasion_datasets`

The seventh topic currently groups negotiation, English/German sales-call examples, and Telefonakquise because those sources often overlap. We can split it later if the source library becomes large enough.

## What It Creates

RAG-001 creates:

- a source manifest template with one source slot per topic
- a NotebookLM extraction prompt
- a chunk schema for NotebookLM output
- a validator for source IDs, topic IDs, rights status, source excerpts, and raw-text boundaries
- a generated source-tracked knowledge-base preview

## Chunk Rules

Each chunk must include:

- `chunk_id`
- `topic_ids`
- `source_ids`
- `language`
- `sales_stage`
- `principle`
- `application`
- `when_not_to_use`
- `example_phrases`
- `emotional_cues`
- `compliance_notes`
- `evidence_type`
- `confidence`
- `citation_note`

Short `source_excerpt` values are allowed only when needed and must stay under the configured word limit. Blank is preferred.

## Boundaries

Allowed:

- public source metadata
- user-curated source lists
- NotebookLM-generated paraphrased notes
- source-tracked short examples
- synthetic demo chunks for validation

Forbidden:

- long copied passages
- pasted full transcripts
- copied book chapters
- raw private call-center data
- raw private customer data
- API keys
- unsourced sales claims
- runtime retrieval without a later reviewed checkpoint

## Run

Dry-run source-intake bridge:

```powershell
python scripts\run_rag_001_notebooklm_source_intake.py
```

Validate:

```powershell
python scripts\validate_rag_001_notebooklm_source_intake.py
```

## Output

Default output folder:

```text
research\experiments\generated\RAG-001-notebooklm-source-intake-bridge\
```

Expected files:

- `result.json`
- `report.md`

## Human Workflow

1. Replace source slots with real source metadata.
2. Add the sources to NotebookLM.
3. Paste the generated extraction prompt into NotebookLM.
4. Ask NotebookLM for JSON chunks only.
5. Import the JSON chunks through the validator.
6. Promote only validated, source-tracked, paraphrased chunks into the local RAG base.

## Product Meaning

RAG-001 starts the sales brain without compromising the architecture:

```text
reusable sales-agent core
  + SalesCampaign guardrails
  + source-tracked RAG knowledge
  + voice delivery layers
```

The RAG base should improve wording, objection handling, ethical persuasion, and semantic focus planning later. It should not override campaign facts, compliance rules, or human handoff boundaries.
