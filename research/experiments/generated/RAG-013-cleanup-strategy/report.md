# RAG-013 Cleanup Strategy

RAG-013 partitions the remaining RAG cleanup work. Runtime retrieval remains disabled.

## Summary

- Recommended next checkpoint: `RAG-014-source-mapped-quote-followup`
- Remaining source-mapping chunks: `58`
- Remaining source-mapping groups: `43`
- Remaining original quote-clearance chunks: `30`
- Quote follow-ups from accepted source mappings: `5`
- Known cleanup work count before runtime: `93`
- Latent quote follow-up after remaining source mapping: `21`
- Cleanup decisions applied now: `0`
- Auto-promoted chunks: `0`
- Runtime retrieval enabled: `False`
- Chunk import enabled: `False`

## Strategy Stages

| Checkpoint | Lane | Target chunks | Objective |
| --- | --- | ---: | --- |
| `RAG-014-source-mapped-quote-followup` | `source_mapped_quote_followup` | `5` | Clear or reject the quote dependencies created by RAG-012 accepted source mappings. |
| `RAG-015-source-mapping-batches` | `source_mapping` | `58` | Review remaining source-title groups and map them to existing or newly reviewed source records. |
| `RAG-016-quote-clearance-batches` | `quote_clearance` | `51` | Rewrite or reject remaining quote-dependent candidates as project-owned rules. |
| `RAG-017-clean-candidate-reaudit` | `pre_runtime_audit` | `0` | Re-audit clean candidates before any runtime-off retrieval harness is considered. |

## RAG-014 Follow-Up Cards

| Chunk ID | Accepted source | Action |
| --- | --- | --- |
| `rag005-chunk-081` | `rag004-source-025` Behavioral Science Concepts (BE Hub) | create_project_owned_paraphrase_or_reject |
| `rag005-chunk-084` | `rag004-source-025` Behavioral Science Concepts (BE Hub) | create_project_owned_paraphrase_or_reject |
| `rag005-chunk-005` | `rag004-source-051` Jason Bay (Sell Better) | create_project_owned_paraphrase_or_reject |
| `rag005-chunk-006` | `rag004-source-051` Jason Bay (Sell Better) | create_project_owned_paraphrase_or_reject |
| `rag005-chunk-003` | `rag004-source-028` Cognism Hub/Scripts | create_project_owned_paraphrase_or_reject |

## Source-Mapping Batch Preview

| Source title | Remaining chunks | Review mode |
| --- | ---: | --- |
| Discovery Masterclass: Everything You Need to Run a Perfect Discovery Call | `5` | `source_metadata_creation_or_manual_mapping_review` |
| Never Split The Difference / Chris Voss Summary Cheat-Sheet | `4` | `source_metadata_creation_or_manual_mapping_review` |
| Social Influence Dialogue Systems | `3` | `source_metadata_creation_or_manual_mapping_review` |
| 24 Techniques for Closing the Sale | `2` | `source_metadata_creation_or_manual_mapping_review` |
| Einwandbehandlung im Verkauf (zu teuer, keine Zeit & Co.) (\#derLÖSER) | `2` | `source_metadata_creation_or_manual_mapping_review` |
| Master B2B Sales Negotiation in 46 Minutes | `2` | `source_metadata_creation_or_manual_mapping_review` |
| Never Split the Difference | `2` | `source_metadata_creation_or_manual_mapping_review` |
| Telefonakquise - Der Leitfaden / Kaltakquise (\#derLÖSER) | `2` | `source_metadata_creation_or_manual_mapping_review` |
| Telefonakquise-Leitfaden: 11 Vorlagen, Beispiele (Pipedrive) | `2` | `source_metadata_creation_or_manual_mapping_review` |
| 10 Sales Training Methodologies Compared (2026) / Salesmotion | `1` | `source_metadata_creation_or_manual_mapping_review` |
| 16 Best Closing Techniques | `1` | `source_metadata_creation_or_manual_mapping_review` |
| 18 Steps to a Successful Discovery Call \+ Free Discovery Call Checklist | `1` | `source_metadata_creation_or_manual_mapping_review` |

## Quote-Clearance Lane Counts

- `ethical_persuasion`: `11`
- `voice_delivery`: `19`

## Boundaries

- Runtime retrieval remains disabled.
- Chunk import remains disabled.
- No chunks are auto-promoted.
- No cleanup decisions are applied by this strategy packet.
- No provider or NotebookLM API calls are made.
- No private customer data is used.
- No source excerpt text is stored.
