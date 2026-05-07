# RAG-016 Quote-Clearance Batches Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the RAG-016 quote-clearance batch artifact that organizes all remaining original quote-dependent chunks after RAG-015.

**Architecture:** Add a validator-first Python checkpoint matching the existing RAG-013 through RAG-015 pattern. The builder reads public generated artifacts, excludes RAG-012 accepted quote-clearance items from the RAG-009 quote-clearance queue, groups the remaining rows into ethical-persuasion and voice-delivery review batches, and emits JSON/Markdown without mutating older artifacts.

**Tech Stack:** Python standard library, local JSON/Markdown artifacts, project setup validators.

---

### Task 1: Validator Contract

**Files:**
- Create: `scripts/validate_rag_016_quote_clearance_batches.py`

- [ ] Write a validator that fails while `scripts/rag_quote_clearance_batches.py` is absent.
- [ ] Use fixture RAG-015/RAG-013/RAG-012/RAG-009/case inputs.
- [ ] Assert quote-clearance chunk counts, ethical-persuasion count, voice-delivery count, topic-batch counts, and no cleanup decisions applied.
- [ ] Assert runtime retrieval, chunk import, provider calls, private-data reads, auto-promotion, source-excerpt fields, and runtime eligibility stay absent.
- [ ] Run `python scripts\validate_rag_016_quote_clearance_batches.py` and confirm the first failure is `RAG-016 quote-clearance batches module is missing.`

### Task 2: Builder And Runner

**Files:**
- Create: `scripts/rag_quote_clearance_batches.py`
- Create: `scripts/run_rag_016_quote_clearance_batches.py`
- Create: `research/experiments/cases/rag-016-quote-clearance-batches.json`

- [ ] Add project-root path resolution that rejects paths outside the repo and under private-data directories.
- [ ] Validate RAG-015, RAG-013, RAG-012, RAG-009, and case IDs.
- [ ] Require RAG-015 to have applied zero source-mapping decisions and enabled no runtime retrieval.
- [ ] Exclude RAG-012 accepted quote-clearance chunk IDs from the RAG-009 original quote-clearance queue.
- [ ] Build batch cards with source title, source IDs, topic IDs, lane, batch ID, review action, and review guardrail.
- [ ] Render JSON and Markdown reports.

### Task 3: Docs And Gates

**Files:**
- Create: `docs/product/RAG_016_QUOTE_CLEARANCE_BATCHES.md`
- Modify: `docs/product/COMMANDS.md`
- Modify: `scripts/check_setup.py`
- Modify: `scripts/validate_check_setup.py`
- Modify: `docs/thesis/ROADMAP.md`
- Modify: `docs/thesis/METHODOLOGY_LOG.md`

- [ ] Document the command, output folder, official counts, no-decision boundary, and no-runtime boundary.
- [ ] Add RAG-016 checks to setup.
- [ ] Move roadmap current checkpoint to the RAG-016A quote-clearance decision slice.
- [ ] Add a methodology-log entry for the RAG-016 batching decision.

### Task 4: Verification

**Commands:**

```powershell
python scripts\validate_rag_015_source_mapping_batches.py
python scripts\validate_rag_016_quote_clearance_batches.py
python scripts\validate_check_setup.py
python scripts\check_setup.py --json
python scripts\check_thesis_update_gate.py
```

Boundary greps:

```powershell
rg -n '"runtime_retrieval_enabled": true|"chunk_import_enabled": true|"retrieval_used_in_runtime": true|"runtime_use_allowed": true|"runtime_eligible_now": true|"retrieval_eligible_now": true|"auto_promote_allowed": true|"provider_calls_made": true|"notebooklm_api_used": true|"private_customer_data_used": true|"reads_data_private": true' scripts\rag_quote_clearance_batches.py scripts\run_rag_016_quote_clearance_batches.py docs\product\RAG_016_QUOTE_CLEARANCE_BATCHES.md research\experiments\cases\rag-016-quote-clearance-batches.json research\experiments\generated\RAG-016-quote-clearance-batches
rg -n 'data/private|"source_excerpt_text"\s*:|"source_excerpt"\s*:' docs\product\RAG_016_QUOTE_CLEARANCE_BATCHES.md research\experiments\cases\rag-016-quote-clearance-batches.json research\experiments\generated\RAG-016-quote-clearance-batches
```
