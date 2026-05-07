# RAG-012 Accepted Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the RAG-012 accepted cleanup artifact from RAG-011 while keeping runtime retrieval disabled.

**Architecture:** Add a small builder module, CLI runner, validator, case config, official generated artifact, product doc, setup wiring, and thesis notes. The builder reads only project-local public/generated RAG artifacts and emits a new review artifact without mutating prior checkpoints.

**Tech Stack:** Python standard library, JSON/Markdown artifacts, project-local validation scripts.

---

### Task 1: Validator Contract

**Files:**
- Create: `scripts/validate_rag_012_accepted_cleanup.py`

- [ ] Write a validator that fails while the RAG-012 module is absent.
- [ ] Use synthetic fixture inputs with one accepted source-mapping group and two accepted quote-clearance cards.
- [ ] Assert no runtime retrieval, chunk import, provider calls, private-data reads, or source excerpt fields.
- [ ] Assert the official artifact, if present, contains `17` accepted cleanup decisions and leaves runtime disabled.
- [ ] Run `python scripts\validate_rag_012_accepted_cleanup.py` and confirm the first failure is `RAG-012 accepted cleanup module is missing.`

### Task 2: Builder And Runner

**Files:**
- Create: `scripts/rag_accepted_cleanup.py`
- Create: `scripts/run_rag_012_accepted_cleanup.py`
- Create: `research/experiments/cases/rag-012-accepted-cleanup.json`

- [ ] Implement path resolution that rejects paths outside the project root and under `data/private` or `data/private-restricted`.
- [ ] Validate RAG-011 and RAG-009 IDs and disabled runtime boundaries.
- [ ] Convert RAG-011 source-mapping candidates into accepted metadata decisions only.
- [ ] Convert the twelve selected quote-clearance cards into fixed project-owned paraphrases with safe applications and guardrails.
- [ ] Keep every emitted item `runtime_eligible_now: false` and `retrieval_eligible_now: false`.
- [ ] Run the validator and then `python scripts\run_rag_012_accepted_cleanup.py`.

### Task 3: Documentation And Setup Wiring

**Files:**
- Create: `docs/product/RAG_012_ACCEPTED_CLEANUP.md`
- Modify: `docs/product/COMMANDS.md`
- Modify: `scripts/check_setup.py`
- Modify: `scripts/validate_check_setup.py`
- Modify: `docs/thesis/ROADMAP.md`
- Modify: `docs/thesis/METHODOLOGY_LOG.md`

- [ ] Document the RAG-012 command, output folder, accepted cleanup counts, and boundaries.
- [ ] Add RAG-012 doc/script/case checks to setup.
- [ ] Move roadmap current checkpoint forward after RAG-012 and add the completed checkpoint summary.
- [ ] Add a methodology-log entry describing the data used, outputs, learned blocker counts, and no-runtime boundary.

### Task 4: Verification

**Commands:**

```powershell
python scripts\validate_rag_011_blocker_cleanup_packet.py
python scripts\validate_rag_012_accepted_cleanup.py
python scripts\validate_check_setup.py
python scripts\check_setup.py --json
python scripts\check_thesis_update_gate.py
```

Boundary greps:

```powershell
rg -n '"runtime_retrieval_enabled": true|"chunk_import_enabled": true|"retrieval_used_in_runtime": true|"runtime_use_allowed": true|"runtime_eligible_now": true|"retrieval_eligible_now": true|"auto_promote_allowed": true|"provider_calls_made": true|"notebooklm_api_used": true|"private_customer_data_used": true|"reads_data_private": true' scripts\rag_accepted_cleanup.py scripts\run_rag_012_accepted_cleanup.py docs\product\RAG_012_ACCEPTED_CLEANUP.md research\experiments\cases\rag-012-accepted-cleanup.json research\experiments\generated\RAG-012-accepted-cleanup
rg -n 'data/private|"source_excerpt_text"\s*:|"source_excerpt"\s*:' docs\product\RAG_012_ACCEPTED_CLEANUP.md research\experiments\cases\rag-012-accepted-cleanup.json research\experiments\generated\RAG-012-accepted-cleanup
```
