# RAG-010 Reviewed Expansion Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build RAG-010 as an offline reviewed expansion slice from the four clean RAG-009 next-promotion candidates.

**Architecture:** Add one deterministic Python builder that reads the RAG-009 coverage artifact and case config, validates the four expected candidate chunks, emits project-owned paraphrased knowledge items, and renders a Markdown report. Add a CLI runner, validator, case file, product docs, generated artifacts, and command/setup/thesis wiring. Runtime retrieval, chunk import, provider calls, NotebookLM calls, private data reads, embeddings, vector storage, and auto-promotion stay disabled.

**Tech Stack:** Python standard library, JSON artifacts, Markdown reports, existing project `scripts/check_setup.py`, existing RAG artifact conventions.

---

### Task 1: Validator

**Files:**
- Create: `scripts/validate_rag_010_reviewed_expansion_slice.py`

- [ ] **Step 1: Write the failing validator**

Create a validator that requires:

- `scripts/rag_reviewed_expansion_slice.py` exists.
- `scripts/run_rag_010_reviewed_expansion_slice.py` exists.
- `docs/product/RAG_010_REVIEWED_EXPANSION_SLICE.md` exists.
- `research/experiments/cases/rag-010-reviewed-expansion-slice.json` exists.
- Module constant `RAG_REVIEWED_EXPANSION_SLICE_ID == "RAG-010-reviewed-expansion-slice"`.
- `build_reviewed_expansion_slice(rag009_result_path, case_path, root=ROOT)`.
- `render_reviewed_expansion_slice_report(payload)`.
- A fixture RAG-009 payload with four candidates produces `4` reviewed items, `3` response-wording items, `1` voice-delivery item, `0` rejected items, no source excerpt text, and all runtime flags false.

- [ ] **Step 2: Verify RED**

Run:

```powershell
python scripts\validate_rag_010_reviewed_expansion_slice.py
```

Expected: fails because the module is missing.

- [ ] **Step 3: Commit validator**

```powershell
git add -- scripts\validate_rag_010_reviewed_expansion_slice.py
git commit -m "test: add RAG-010 reviewed expansion validator" -- scripts\validate_rag_010_reviewed_expansion_slice.py
```

### Task 2: Builder

**Files:**
- Create: `scripts/rag_reviewed_expansion_slice.py`

- [ ] **Step 1: Implement minimal builder**

Implement:

```python
RAG_REVIEWED_EXPANSION_SLICE_ID = "RAG-010-reviewed-expansion-slice"

def build_reviewed_expansion_slice(rag009_result_path, case_path, *, root=None) -> dict[str, Any]:
    ...

def render_reviewed_expansion_slice_report(payload: dict[str, Any]) -> str:
    ...
```

The builder must:

- Reject paths outside the project root and under `data/private` or `data/private-restricted`.
- Load RAG-009 next-promotion candidates.
- Require exactly the case-selected chunk IDs: `rag005-chunk-029`, `rag005-chunk-030`, `rag005-chunk-031`, `rag005-chunk-036`.
- Create project-owned paraphrases from static review rules.
- Mark `rag005-chunk-036` as `voice_delivery` and advisory-only.
- Keep every item `runtime_eligible_now: false`, `retrieval_eligible_now: false`.
- Store no source excerpt text fields.

- [ ] **Step 2: Verify GREEN**

Run:

```powershell
python scripts\validate_rag_010_reviewed_expansion_slice.py
```

Expected: runner/doc/case missing after module checks pass.

- [ ] **Step 3: Commit builder**

```powershell
git add -- scripts\rag_reviewed_expansion_slice.py
git commit -m "feat: add RAG-010 reviewed expansion builder" -- scripts\rag_reviewed_expansion_slice.py
```

### Task 3: Runner, Case, Product Doc

**Files:**
- Create: `scripts/run_rag_010_reviewed_expansion_slice.py`
- Create: `research/experiments/cases/rag-010-reviewed-expansion-slice.json`
- Create: `docs/product/RAG_010_REVIEWED_EXPANSION_SLICE.md`

- [ ] **Step 1: Add runner**

Default input/output:

```text
research\experiments\generated\RAG-009-all-source-review-coverage\result.json
research\experiments\cases\rag-010-reviewed-expansion-slice.json
research\experiments\generated\RAG-010-reviewed-expansion-slice\
```

Support `--rag009-result`, `--case`, `--out`, and `--report-out`.

- [ ] **Step 2: Add case config**

Case config selects the four RAG-009 candidates and repeats runtime-disabled boundaries.

- [ ] **Step 3: Add product doc**

Document purpose, commands, output, candidate review decisions, and no-runtime boundary.

- [ ] **Step 4: Validate and commit**

Run:

```powershell
python scripts\validate_rag_010_reviewed_expansion_slice.py
```

Expected: validation passes.

Commit:

```powershell
git add -- scripts\run_rag_010_reviewed_expansion_slice.py research\experiments\cases\rag-010-reviewed-expansion-slice.json docs\product\RAG_010_REVIEWED_EXPANSION_SLICE.md
git commit -m "feat: add RAG-010 reviewed expansion runner" -- scripts\run_rag_010_reviewed_expansion_slice.py research\experiments\cases\rag-010-reviewed-expansion-slice.json docs\product\RAG_010_REVIEWED_EXPANSION_SLICE.md
```

### Task 4: Official Artifacts

**Files:**
- Create: `research/experiments/generated/RAG-010-reviewed-expansion-slice/result.json`
- Create: `research/experiments/generated/RAG-010-reviewed-expansion-slice/report.md`

- [ ] **Step 1: Generate artifacts**

Run:

```powershell
python scripts\run_rag_010_reviewed_expansion_slice.py
```

Expected: `knowledge_item_count: 4`, `response_wording: 3`, `voice_delivery: 1`, runtime false.

- [ ] **Step 2: Validate and commit artifacts**

Run:

```powershell
python scripts\validate_rag_010_reviewed_expansion_slice.py
```

Commit:

```powershell
git add -- research\experiments\generated\RAG-010-reviewed-expansion-slice
git commit -m "test: add RAG-010 reviewed expansion artifacts" -- research\experiments\generated\RAG-010-reviewed-expansion-slice
```

### Task 5: Wiring and Final Verification

**Files:**
- Modify: `docs/product/COMMANDS.md`
- Modify: `scripts/check_setup.py`
- Modify: `docs/thesis/ROADMAP.md`
- Modify: `docs/thesis/METHODOLOGY_LOG.md`

- [ ] **Step 1: Wire commands/setup/thesis**

Add RAG-010 command docs, required-file checks, roadmap completion, and methodology entry.

- [ ] **Step 2: Final verification**

Run:

```powershell
python scripts\validate_rag_009_all_source_review_coverage.py
python scripts\validate_rag_010_reviewed_expansion_slice.py
python scripts\validate_check_setup.py
python scripts\check_setup.py --json
python scripts\check_thesis_update_gate.py
```

Run boundary grep for runtime-enabled flags, private paths, and source excerpt fields over the RAG-010 surface.

- [ ] **Step 3: Commit wiring**

```powershell
git add -- docs\product\COMMANDS.md scripts\check_setup.py docs\thesis\ROADMAP.md docs\thesis\METHODOLOGY_LOG.md
git commit -m "docs: document RAG-010 reviewed expansion checkpoint" -- docs\product\COMMANDS.md scripts\check_setup.py docs\thesis\ROADMAP.md docs\thesis\METHODOLOGY_LOG.md
```
