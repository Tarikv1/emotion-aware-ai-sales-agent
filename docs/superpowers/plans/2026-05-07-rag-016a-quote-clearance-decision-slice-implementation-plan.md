# RAG-016A Quote-Clearance Decision Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Record the first RAG-016 quote-clearance decision slice by accepting the ethical-persuasion batch as project-owned low-pressure rules.

**Architecture:** Add a validator-first Python checkpoint matching the existing RAG-012/RAG-014 pattern. The builder reads the RAG-016 batch artifact, validates that the selected ethical-persuasion batch is fully reviewed, converts each accepted card into a fixed project-owned rule, and emits JSON/Markdown without mutating older artifacts.

**Tech Stack:** Python standard library, local JSON/Markdown artifacts, project setup validators.

---

### Task 1: Validator Contract

**Files:**
- Create: `scripts/validate_rag_016a_quote_clearance_decision_slice.py`

- [ ] Write a validator that fails while `scripts/rag_quote_clearance_decision_slice.py` is absent.
- [ ] Use fixture RAG-016/RAG-009/case inputs.
- [ ] Assert accepted count, rejected count, remaining quote-clearance count, lane counts, and no runtime eligibility.
- [ ] Assert runtime retrieval, chunk import, provider calls, private-data reads, auto-promotion, and source-excerpt fields stay absent.
- [ ] Run `python scripts\validate_rag_016a_quote_clearance_decision_slice.py` and confirm the first failure is `RAG-016A quote-clearance decision slice module is missing.`

### Task 2: Builder And Runner

**Files:**
- Create: `scripts/rag_quote_clearance_decision_slice.py`
- Create: `scripts/run_rag_016a_quote_clearance_decision_slice.py`
- Create: `research/experiments/cases/rag-016a-quote-clearance-decision-slice.json`

- [ ] Add project-root path resolution that rejects paths outside the repo and under private-data directories.
- [ ] Validate RAG-016, RAG-009, and case IDs.
- [ ] Require the selected RAG-016 priority batch to be fully reviewed by the case file.
- [ ] Build accepted project-owned rules for all selected ethical-persuasion chunks.
- [ ] Leave non-selected voice-delivery cards pending.
- [ ] Render JSON and Markdown reports.

### Task 3: Docs And Gates

**Files:**
- Create: `docs/product/RAG_016A_QUOTE_CLEARANCE_DECISION_SLICE.md`
- Modify: `docs/product/COMMANDS.md`
- Modify: `scripts/check_setup.py`
- Modify: `scripts/validate_check_setup.py`
- Modify: `docs/thesis/ROADMAP.md`
- Modify: `docs/thesis/METHODOLOGY_LOG.md`

- [ ] Document the command, output folder, official counts, accepted rules, remaining voice-delivery queue, and no-runtime boundary.
- [ ] Add RAG-016A checks to setup.
- [ ] Move roadmap current checkpoint to RAG-016B voice-delivery quote-clearance review.
- [ ] Add a methodology-log entry for the RAG-016A acceptance decision.

### Task 4: Verification

**Commands:**

```powershell
python scripts\validate_rag_016_quote_clearance_batches.py
python scripts\validate_rag_016a_quote_clearance_decision_slice.py
python scripts\validate_check_setup.py
python scripts\check_setup.py --json
python scripts\check_thesis_update_gate.py
```

Boundary greps:

```powershell
rg -n '"runtime_retrieval_enabled": true|"chunk_import_enabled": true|"retrieval_used_in_runtime": true|"runtime_use_allowed": true|"runtime_eligible_now": true|"retrieval_eligible_now": true|"auto_promote_allowed": true|"provider_calls_made": true|"notebooklm_api_used": true|"private_customer_data_used": true|"reads_data_private": true' scripts\rag_quote_clearance_decision_slice.py scripts\run_rag_016a_quote_clearance_decision_slice.py docs\product\RAG_016A_QUOTE_CLEARANCE_DECISION_SLICE.md research\experiments\cases\rag-016a-quote-clearance-decision-slice.json research\experiments\generated\RAG-016A-quote-clearance-decision-slice
rg -n 'data/private|"source_excerpt_text"\s*:|"source_excerpt"\s*:' docs\product\RAG_016A_QUOTE_CLEARANCE_DECISION_SLICE.md research\experiments\cases\rag-016a-quote-clearance-decision-slice.json research\experiments\generated\RAG-016A-quote-clearance-decision-slice
```
