# RAG-015 Source-Mapping Batches Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the RAG-015 source-mapping batch artifact that organizes all remaining source-title cleanup work after RAG-014.

**Architecture:** Add a validator-first Python checkpoint matching the existing RAG-013/RAG-014 pattern. The builder reads public generated artifacts, excludes source mappings already resolved by RAG-012/RAG-014, groups the remaining RAG-006 source-mapping queue into review batches, and emits JSON/Markdown without mutating older artifacts.

**Tech Stack:** Python standard library, local JSON/Markdown artifacts, project setup validators.

---

### Task 1: Validator Contract

**Files:**
- Create: `scripts/validate_rag_015_source_mapping_batches.py`

- [ ] Write a validator that fails while `scripts/rag_source_mapping_batches.py` is absent.
- [ ] Use fixture RAG-014/RAG-013/RAG-006/RAG-009/case inputs.
- [ ] Assert source-mapping group/chunk counts, priority batch counts, latent quote follow-up counts, and no cleanup decisions applied.
- [ ] Assert runtime retrieval, chunk import, provider calls, private-data reads, auto-promotion, and source excerpt fields stay absent.
- [ ] Run `python scripts\validate_rag_015_source_mapping_batches.py` and confirm the first failure is `RAG-015 source-mapping batches module is missing.`

### Task 2: Builder And Runner

**Files:**
- Create: `scripts/rag_source_mapping_batches.py`
- Create: `scripts/run_rag_015_source_mapping_batches.py`
- Create: `research/experiments/cases/rag-015-source-mapping-batches.json`

- [ ] Add project-root path resolution that rejects paths outside the repo and under private-data directories.
- [ ] Validate RAG-014, RAG-013, RAG-006, RAG-009, and case IDs.
- [ ] Require RAG-014 source-mapped quote follow-ups to be fully cleared before batching source mappings.
- [ ] Exclude RAG-014 source-mapped follow-up chunks from the remaining RAG-006 source-mapping queue.
- [ ] Build one review group per remaining source title with chunk IDs, topic IDs, candidate source suggestions, priority batch, and latent quote-follow-up count.
- [ ] Render JSON and Markdown reports.

### Task 3: Docs And Gates

**Files:**
- Create: `docs/product/RAG_015_SOURCE_MAPPING_BATCHES.md`
- Modify: `docs/product/COMMANDS.md`
- Modify: `scripts/check_setup.py`
- Modify: `scripts/validate_check_setup.py`
- Modify: `docs/thesis/ROADMAP.md`
- Modify: `docs/thesis/METHODOLOGY_LOG.md`

- [ ] Document the command, output folder, official counts, no-decision boundary, and no-runtime boundary.
- [ ] Add RAG-015 checks to setup.
- [ ] Move roadmap current checkpoint to RAG-016 quote-clearance batches.
- [ ] Add a methodology-log entry for the RAG-015 batching decision.

### Task 4: Verification

**Commands:**

```powershell
python scripts\validate_rag_014_source_mapped_quote_followup.py
python scripts\validate_rag_015_source_mapping_batches.py
python scripts\validate_check_setup.py
python scripts\check_setup.py --json
python scripts\check_thesis_update_gate.py
```

Boundary greps:

```powershell
rg -n '"runtime_retrieval_enabled": true|"chunk_import_enabled": true|"retrieval_used_in_runtime": true|"runtime_use_allowed": true|"runtime_eligible_now": true|"retrieval_eligible_now": true|"auto_promote_allowed": true|"provider_calls_made": true|"notebooklm_api_used": true|"private_customer_data_used": true|"reads_data_private": true' scripts\rag_source_mapping_batches.py scripts\run_rag_015_source_mapping_batches.py docs\product\RAG_015_SOURCE_MAPPING_BATCHES.md research\experiments\cases\rag-015-source-mapping-batches.json research\experiments\generated\RAG-015-source-mapping-batches
rg -n 'data/private|"source_excerpt_text"\s*:|"source_excerpt"\s*:' docs\product\RAG_015_SOURCE_MAPPING_BATCHES.md research\experiments\cases\rag-015-source-mapping-batches.json research\experiments\generated\RAG-015-source-mapping-batches
```
