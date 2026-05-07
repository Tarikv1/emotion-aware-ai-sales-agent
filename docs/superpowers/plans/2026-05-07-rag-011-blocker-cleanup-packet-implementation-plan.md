# RAG-011 Blocker Cleanup Packet Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build RAG-011 as an offline blocker-cleanup packet that narrows source-mapping and quote-clearance review work without enabling runtime retrieval.

**Architecture:** Add one deterministic Python builder that reads RAG-009 coverage, RAG-006 review packet, and a RAG-011 case config. It emits high-confidence source-mapping proposals from RAG-006 suggestions and bounded quote-clearance review cards from RAG-009 blocked quote rows. A CLI runner, validator, case file, product docs, generated artifacts, setup wiring, and thesis docs complete the checkpoint.

**Tech Stack:** Python standard library, JSON artifacts, Markdown reports, existing project setup/thesis validators.

---

### Task 1: Validator

**Files:**
- Create: `scripts/validate_rag_011_blocker_cleanup_packet.py`

- [ ] **Step 1: Write failing validator**

The validator must require:

- module constant `RAG_BLOCKER_CLEANUP_PACKET_ID == "RAG-011-blocker-cleanup-packet"`
- `build_blocker_cleanup_packet(rag009_result_path, rag006_packet_path, case_path, root=ROOT)`
- `render_blocker_cleanup_packet_report(payload)`
- runner, case file, and product doc exist
- fixture output has:
  - `source_mapping_blocker_count == 3`
  - `source_mapping_candidate_group_count == 1`
  - `source_mapping_candidate_chunk_count == 2`
  - `quote_clearance_blocker_count == 3`
  - `quote_clearance_review_card_count == 2`
  - `blockers_resolved_now == 0`
  - all runtime/provider/private/source-excerpt boundaries false

- [ ] **Step 2: Verify RED**

Run:

```powershell
python scripts\validate_rag_011_blocker_cleanup_packet.py
```

Expected: fails because the RAG-011 module is missing.

- [ ] **Step 3: Commit validator**

```powershell
git add -- scripts\validate_rag_011_blocker_cleanup_packet.py
git commit -m "test: add RAG-011 blocker cleanup validator" -- scripts\validate_rag_011_blocker_cleanup_packet.py
```

### Task 2: Builder

**Files:**
- Create: `scripts/rag_blocker_cleanup_packet.py`

- [ ] **Step 1: Implement builder**

Implement:

```python
RAG_BLOCKER_CLEANUP_PACKET_ID = "RAG-011-blocker-cleanup-packet"

def build_blocker_cleanup_packet(rag009_result_path, rag006_packet_path, case_path, *, root=None) -> dict[str, Any]:
    ...

def render_blocker_cleanup_packet_report(payload: dict[str, Any]) -> str:
    ...
```

Rules:

- reject paths outside project root and under `data/private` or `data/private-restricted`
- require RAG-009 and RAG-006 runtime boundaries false
- source mapping proposals come only from `candidate_source_suggestions` with score at or above `min_source_suggestion_score`
- quote clearance cards come from RAG-009 `review_queues.quote_clearance_queue`, enriched by `chunk_coverage`
- quote cards must never copy source excerpt text
- all proposed actions require human acceptance
- no blockers are marked resolved now

- [ ] **Step 2: Verify builder**

Run:

```powershell
python scripts\validate_rag_011_blocker_cleanup_packet.py
```

Expected: runner/doc/case missing after module checks pass.

- [ ] **Step 3: Commit builder**

```powershell
git add -- scripts\rag_blocker_cleanup_packet.py
git commit -m "feat: add RAG-011 blocker cleanup builder" -- scripts\rag_blocker_cleanup_packet.py
```

### Task 3: Runner, Case, Product Doc

**Files:**
- Create: `scripts/run_rag_011_blocker_cleanup_packet.py`
- Create: `research/experiments/cases/rag-011-blocker-cleanup-packet.json`
- Create: `docs/product/RAG_011_BLOCKER_CLEANUP_PACKET.md`

- [ ] **Step 1: Add runner**

Default inputs and output:

```text
research\experiments\generated\RAG-009-all-source-review-coverage\result.json
research\experiments\generated\RAG-006-chunk-review-packet\result.json
research\experiments\cases\rag-011-blocker-cleanup-packet.json
research\experiments\generated\RAG-011-blocker-cleanup-packet\
```

- [ ] **Step 2: Add case config**

Use:

```json
{
  "blocker_cleanup_packet_id": "RAG-011-blocker-cleanup-packet",
  "min_source_suggestion_score": 0.55,
  "max_quote_clearance_cards": 12,
  "runtime_retrieval_enabled": false,
  "retrieval_used_in_runtime": false,
  "chunk_import_enabled": false,
  "auto_promotion_enabled": false
}
```

- [ ] **Step 3: Add product doc**

Document purpose, commands, default output, cleanup lanes, and no-runtime boundary.

- [ ] **Step 4: Validate and commit**

Run:

```powershell
python scripts\validate_rag_011_blocker_cleanup_packet.py
```

Commit:

```powershell
git add -- scripts\run_rag_011_blocker_cleanup_packet.py research\experiments\cases\rag-011-blocker-cleanup-packet.json docs\product\RAG_011_BLOCKER_CLEANUP_PACKET.md
git commit -m "feat: add RAG-011 blocker cleanup runner" -- scripts\run_rag_011_blocker_cleanup_packet.py research\experiments\cases\rag-011-blocker-cleanup-packet.json docs\product\RAG_011_BLOCKER_CLEANUP_PACKET.md
```

### Task 4: Official Artifacts

**Files:**
- Create: `research/experiments/generated/RAG-011-blocker-cleanup-packet/result.json`
- Create: `research/experiments/generated/RAG-011-blocker-cleanup-packet/report.md`

- [ ] **Step 1: Generate artifacts**

Run:

```powershell
python scripts\run_rag_011_blocker_cleanup_packet.py
```

Expected: summary reports `63` source-mapping blockers, `42` quote-clearance blockers, `blockers_resolved_now: 0`, and all runtime flags false.

- [ ] **Step 2: Validate and commit artifacts**

Run:

```powershell
python scripts\validate_rag_011_blocker_cleanup_packet.py
```

Commit:

```powershell
git add -- research\experiments\generated\RAG-011-blocker-cleanup-packet
git commit -m "test: add RAG-011 blocker cleanup artifacts" -- research\experiments\generated\RAG-011-blocker-cleanup-packet
```

### Task 5: Wiring and Verification

**Files:**
- Modify: `docs/product/COMMANDS.md`
- Modify: `scripts/check_setup.py`
- Modify: `docs/thesis/ROADMAP.md`
- Modify: `docs/thesis/METHODOLOGY_LOG.md`

- [ ] **Step 1: Wire docs and setup**

Add RAG-011 commands, required-file checks, roadmap completion, and methodology entry.

- [ ] **Step 2: Final verification**

Run:

```powershell
python scripts\validate_rag_010_reviewed_expansion_slice.py
python scripts\validate_rag_011_blocker_cleanup_packet.py
python scripts\validate_check_setup.py
python scripts\check_setup.py --json
python scripts\check_thesis_update_gate.py
```

Run boundary grep for runtime-enabled flags, private paths, and source excerpt fields over the RAG-011 surface.

- [ ] **Step 3: Commit wiring**

```powershell
git add -- docs\product\COMMANDS.md scripts\check_setup.py docs\thesis\ROADMAP.md docs\thesis\METHODOLOGY_LOG.md
git commit -m "docs: document RAG-011 blocker cleanup checkpoint" -- docs\product\COMMANDS.md scripts\check_setup.py docs\thesis\ROADMAP.md docs\thesis\METHODOLOGY_LOG.md
```
