# RAG-002 NotebookLM Extraction Automation Bridge

## Purpose

RAG-002 reduces the manual work of extracting sales knowledge from NotebookLM notebooks.

It does not scrape NotebookLM, call a NotebookLM API, or treat NotebookLM as permanent product memory.

The bridge creates:

- one Configure Chat custom-instructions file
- one NotebookLM Reports / Create report prompt per topic
- one bounded primary extraction prompt per topic
- one bounded gap-check prompt per topic
- a prompt index
- a future import folder for NotebookLM JSON outputs
- a local validation gate that rejects tiny sample batches and incomplete coverage

## Why This Exists

NotebookLM can summarize sources too aggressively. In earlier manual testing, it returned a small batch first and required repeated follow-up prompts.

RAG-002 changes the workflow by making NotebookLM's report-artifact behavior explicit:

- use response length `Longer`
- use NotebookLM Reports / Create report first, not normal chat
- create an exhaustive report file/document that can be exported or copied
- keep that report readable instead of compressing it into JSON strings
- do not return a small sample batch
- review all selected sources for the topic
- include a RAG-ready extraction appendix inside the report
- mark the answer with `END: COMPLETE` only when coverage is complete
- use `NEED_CONTINUATION` if output limits prevent completion

## Prompt Limit

The default prompt character limit is `4500`.

The default Configure Chat custom-instructions limit is `10000`, matching the limit visible in Tarik's NotebookLM UI during the RAG-002 review.

The runner refuses prompt packs that exceed the configured limit. The limit is intentionally conservative because NotebookLM UI limits can vary by feature, account, and plan.

Run with a different limit only after confirming the current NotebookLM input box accepts it:

`python scripts\run_rag_002_notebooklm_extraction_automation.py --prompt-char-limit 4500`

## Workflow

1. Run the local generator.
2. Open the generated prompt index.
3. Open NotebookLM Configure Chat.
4. Select Custom, paste `00-configure-chat-custom-instructions.md`, set response length to `Longer`, and save.
5. Use the topic's `01-create-report-file.md` prompt in NotebookLM Reports / Create report.
6. Export or copy the completed report file after NotebookLM creates it.
7. Use `02-chat-json-extraction.md` only if a stricter JSON handoff is needed after the report exists.
8. If NotebookLM returns `NEED_CONTINUATION`, a partial answer, or a small sample batch, paste the topic's gap-check prompt.
9. Save the final exported report and/or JSON output into the generated import folder.
10. Promote only outputs that pass the local coverage gate.

## Commands

Run from the repo root:

`python scripts\run_rag_002_notebooklm_extraction_automation.py`

Validate:

`python scripts\validate_rag_002_notebooklm_extraction_automation.py`

## Output

Default output folder:

`research/experiments/generated/RAG-002-notebooklm-extraction-automation-bridge`

Key files:

- `result.json`
- `report.md`
- `prompts/00-configure-chat-custom-instructions.md`
- `prompts/PROMPT_INDEX.md`
- `prompts/<topic>/01-create-report-file.md`
- `prompts/<topic>/02-chat-json-extraction.md`
- `prompts/<topic>/03-gap-check.md`
- `imports/README.md`

## Import Gate

A NotebookLM extraction is promotable only if:

- `completion_status` is `complete`
- all selected sources were reviewed
- `small_sample_batch` is `false`
- no more distinct items remain
- `end_marker` is `END: COMPLETE`
- the extraction meets the configured minimum chunk count unless NotebookLM explicitly marks the source material as insufficient
- all chunks use known source IDs and topic IDs

## Boundaries

Allowed:

- public source metadata
- user-curated source lists
- NotebookLM-generated paraphrased reports
- source-tracked short examples
- source IDs, topic IDs, confidence notes, and citation notes

Forbidden:

- long copied passages
- pasted full transcripts
- copied book chapters
- raw private call-center data
- raw private customer data
- API keys
- unsourced sales claims
- runtime retrieval without a later reviewed checkpoint

## Product Meaning

RAG-002 is still an intake bridge, not the sales brain itself.

It prepares source-tracked material for later RAG-003/RAG-runtime work. The reusable sales-agent core remains separate from the source library, and campaign-specific guardrails still decide what the agent may say.
