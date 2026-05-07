# RAG-002 NotebookLM Import Drop Zone

Paste or export NotebookLM JSON outputs here later, one file per topic.

Rules:

- keep raw source text, full transcripts, book chapters, private data, and API keys out of this folder
- import only NotebookLM outputs that include `completion_status`, `coverage_checklist`, and `chunks`
- outputs without `END: COMPLETE` are treated as partial and should be gap-checked before promotion
- small sample batches should not be promoted into the local RAG base
