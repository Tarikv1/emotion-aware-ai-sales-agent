# RAG-013 Cleanup Strategy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the RAG-013 cleanup strategy artifact that partitions the remaining RAG blockers and recommends the next cleanup order.

**Architecture:** Add a validator-first Python checkpoint matching the existing RAG-009 through RAG-012 pattern. The builder reads existing public generated artifacts, emits a new JSON/Markdown strategy packet, and does not mutate older artifacts.

**Tech Stack:** Python standard library, local JSON/Markdown artifacts, project setup validators.

---

### Task 1: Validator Contract

**Files:**
- Create: `scripts/validate_rag_013_cleanup_strategy.py`

- [ ] Write a validator that fails while `scripts/rag_cleanup_strategy.py` is absent.
- [ ] Use fixture RAG-012/RAG-009/RAG-006/case inputs.
- [ ] Assert remaining source-mapping, quote-clearance, and quote-follow-up counts.
- [ ] Assert the recommended next checkpoint is `RAG-014-source-mapped-quote-followup`.
- [ ] Assert runtime retrieval, chunk import, provider calls, private-data reads, and source excerpt fields are absent.
- [ ] Run `python scripts\validate_rag_013_cleanup_strategy.py` and confirm the first failure is `RAG-013 cleanup strategy module is missing.`

### Task 2: Builder And Runner

**Files:**
- Create: `scripts/rag_cleanup_strategy.py`
- Create: `scripts/run_rag_013_cleanup_strategy.py`
- Create: `research/experiments/cases/rag-013-cleanup-strategy.json`

- [ ] Add project-root path resolution that rejects paths outside the repo and under private-data directories.
- [ ] Validate RAG-012, RAG-009, RAG-006, and case IDs.
- [ ] Exclude RAG-012 accepted source mappings from the remaining source-mapping queue.
- [ ] Exclude RAG-012 accepted quote-clearance rewrites from the original quote-clearance queue.
- [ ] Build source-title review batches from RAG-006 source-mapping groups.
- [ ] Build quote follow-up cards from RAG-012 accepted source mappings.
- [ ] Build quote-clearance lane counts from RAG-009 remaining quote rows.
- [ ] Render JSON and Markdown reports.

### Task 3: Docs And Gates

**Files:**
- Create: `docs/product/RAG_013_CLEANUP_STRATEGY.md`
- Modify: `docs/product/COMMANDS.md`
- Modify: `scripts/check_setup.py`
- Modify: `scripts/validate_check_setup.py`
- Modify: `docs/thesis/ROADMAP.md`
- Modify: `docs/thesis/METHODOLOGY_LOG.md`

- [ ] Document the command, output folder, official counts, and no-runtime boundary.
- [ ] Add RAG-013 checks to setup.
- [ ] Move roadmap current checkpoint to RAG-014.
- [ ] Add a methodology-log entry for the strategy decision.

### Task 4: Verification

**Commands:**

```powershell
python scripts\validate_rag_012_accepted_cleanup.py
python scripts\validate_rag_013_cleanup_strategy.py
python scripts\validate_check_setup.py
python scripts\check_setup.py --json
python scripts\check_thesis_update_gate.py
```

Boundary greps:

```powershell
rg -n '"runtime_retrieval_enabled": true|"chunk_import_enabled": true|"retrieval_used_in_runtime": true|"runtime_use_allowed": true|"runtime_eligible_now": true|"retrieval_eligible_now": true|"auto_promote_allowed": true|"provider_calls_made": true|"notebooklm_api_used": true|"private_customer_data_used": true|"reads_data_private": true' scripts\rag_cleanup_strategy.py scripts\run_rag_013_cleanup_strategy.py docs\product\RAG_013_CLEANUP_STRATEGY.md research\experiments\cases\rag-013-cleanup-strategy.json research\experiments\generated\RAG-013-cleanup-strategy
rg -n 'data/private|"source_excerpt_text"\s*:|"source_excerpt"\s*:' docs\product\RAG_013_CLEANUP_STRATEGY.md research\experiments\cases\rag-013-cleanup-strategy.json research\experiments\generated\RAG-013-cleanup-strategy
```
