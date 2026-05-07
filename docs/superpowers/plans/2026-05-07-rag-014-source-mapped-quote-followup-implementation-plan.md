# RAG-014 Source-Mapped Quote Follow-Up Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the RAG-014 review artifact that clears the five quote follow-ups created by RAG-012 accepted source mappings.

**Architecture:** Add a validator-first Python checkpoint matching the existing RAG-012 and RAG-013 pattern. The builder reads existing public generated artifacts, emits a new JSON/Markdown review packet, and does not mutate older artifacts or enable runtime retrieval.

**Tech Stack:** Python standard library, local JSON/Markdown artifacts, project setup validators.

---

### Task 1: Validator Contract

**Files:**
- Create: `scripts/validate_rag_014_source_mapped_quote_followup.py`

- [ ] Write a validator that fails while `scripts/rag_source_mapped_quote_followup.py` is absent.
- [ ] Use fixture RAG-013/RAG-009/case inputs with one accepted and one rejected follow-up.
- [ ] Assert accepted/rejected counts, remaining follow-up count, project-owned paraphrase fields, and rejection fields.
- [ ] Assert runtime retrieval, chunk import, provider calls, private-data reads, auto-promotion, and source excerpt fields stay absent.
- [ ] Run `python scripts\validate_rag_014_source_mapped_quote_followup.py` and confirm the first failure is `RAG-014 source-mapped quote follow-up module is missing.`

### Task 2: Builder And Runner

**Files:**
- Create: `scripts/rag_source_mapped_quote_followup.py`
- Create: `scripts/run_rag_014_source_mapped_quote_followup.py`
- Create: `research/experiments/cases/rag-014-source-mapped-quote-followup.json`

- [ ] Add project-root path resolution that rejects paths outside the repo and under private-data directories.
- [ ] Validate RAG-013, RAG-009, and case IDs.
- [ ] Require accepted and rejected IDs to cover every RAG-013 source-mapped quote follow-up exactly once.
- [ ] Build accepted quote-clearance items from project-owned rules keyed by chunk ID.
- [ ] Build rejected follow-up items for unsafe or pressure-oriented candidates.
- [ ] Render JSON and Markdown reports.

### Task 3: Docs And Gates

**Files:**
- Create: `docs/product/RAG_014_SOURCE_MAPPED_QUOTE_FOLLOWUP.md`
- Modify: `docs/product/COMMANDS.md`
- Modify: `scripts/check_setup.py`
- Modify: `scripts/validate_check_setup.py`
- Modify: `docs/thesis/ROADMAP.md`
- Modify: `docs/thesis/METHODOLOGY_LOG.md`

- [ ] Document the command, output folder, official counts, rejected talk-time dominance candidate, and no-runtime boundary.
- [ ] Add RAG-014 checks to setup.
- [ ] Move roadmap current checkpoint to RAG-015 source-mapping batches.
- [ ] Add a methodology-log entry for the RAG-014 review decision.

### Task 4: Verification

**Commands:**

```powershell
python scripts\validate_rag_013_cleanup_strategy.py
python scripts\validate_rag_014_source_mapped_quote_followup.py
python scripts\validate_check_setup.py
python scripts\check_setup.py --json
python scripts\check_thesis_update_gate.py
```

Boundary greps:

```powershell
rg -n '"runtime_retrieval_enabled": true|"chunk_import_enabled": true|"retrieval_used_in_runtime": true|"runtime_use_allowed": true|"runtime_eligible_now": true|"retrieval_eligible_now": true|"auto_promote_allowed": true|"provider_calls_made": true|"notebooklm_api_used": true|"private_customer_data_used": true|"reads_data_private": true' scripts\rag_source_mapped_quote_followup.py scripts\run_rag_014_source_mapped_quote_followup.py docs\product\RAG_014_SOURCE_MAPPED_QUOTE_FOLLOWUP.md research\experiments\cases\rag-014-source-mapped-quote-followup.json research\experiments\generated\RAG-014-source-mapped-quote-followup
rg -n 'data/private|"source_excerpt_text"\s*:|"source_excerpt"\s*:' docs\product\RAG_014_SOURCE_MAPPED_QUOTE_FOLLOWUP.md research\experiments\cases\rag-014-source-mapped-quote-followup.json research\experiments\generated\RAG-014-source-mapped-quote-followup
```
