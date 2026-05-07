# RAG-008 Guarded Retrieval Policy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a dry-run guarded retrieval-policy checkpoint over RAG-007 reviewed knowledge without enabling runtime retrieval.

**Architecture:** Add one focused policy module, one runner, one validator, one case file, generated JSON/Markdown artifacts, and docs/setup/thesis wiring. The policy reads only the RAG-007 reviewed slice and synthetic query cases, applies deterministic token matching plus hard context blocks, and emits non-runtime candidate retrieval packets.

**Tech Stack:** Python standard library, JSON fixtures, Markdown docs, existing project script/runner/check_setup patterns.

---

## File Structure

- Create `scripts/rag_guarded_retrieval_policy.py`: deterministic policy builder and report renderer.
- Create `scripts/run_rag_008_guarded_retrieval_policy.py`: CLI wrapper with project-root and private-path guards.
- Create `scripts/validate_rag_008_guarded_retrieval_policy.py`: validator with fixture generation, RED/GREEN contract, runner checks, and boundary assertions.
- Create `research/experiments/cases/rag-008-guarded-retrieval-policy.json`: official synthetic retrieval/blocking cases.
- Create `docs/product/RAG_008_GUARDED_RETRIEVAL_POLICY.md`: product checkpoint doc.
- Generate `research/experiments/generated/RAG-008-guarded-retrieval-policy/result.json` and `report.md`.
- Modify `docs/product/COMMANDS.md`: add RAG-008 run/validate commands after RAG-007.
- Modify `scripts/check_setup.py`: add RAG-008 doc/module/runner/validator/case checks.
- Modify `docs/thesis/ROADMAP.md`: mark current checkpoint complete and set next dry-run/runtime-policy follow-up.
- Modify `docs/thesis/METHODOLOGY_LOG.md`: add RAG-008 methodology entry.

## Task 1: Validator First

**Files:**
- Create: `scripts/validate_rag_008_guarded_retrieval_policy.py`

- [ ] **Step 1: Write the failing validator**

Create a validator that:

- writes `.tmp/rag-008-validation/rag007-result.json`
- writes `.tmp/rag-008-validation/case.json`
- imports `rag_guarded_retrieval_policy`
- expects module missing on first run
- validates summary boundaries:
  - `runtime_retrieval_enabled is False`
  - `retrieval_used_in_runtime is False`
  - `chunk_import_enabled is False`
  - `provider_calls_made is False`
  - `notebooklm_api_used is False`
  - `private_customer_data_used is False`
  - `reads_data_private is False`
  - `source_excerpt_text_stored is False`
  - `only_reviewed_rag007_used is True`
- validates retrieval cases:
  - ordinary objection retrieves `rag007-response-yes-and-objection-framing`
  - broad question retrieves response structure items
  - tone uncertainty retrieves `rag007-voice-tone-mismatch-uncertainty`
  - refusal/protected/handoff/private/pressure cases retrieve nothing
- validates every returned item has `citation_trace`, `source_ids`, `match_reasons`, and `runtime_use_allowed: false`

- [ ] **Step 2: Run validator to verify RED**

Run:

```powershell
python scripts\validate_rag_008_guarded_retrieval_policy.py
```

Expected result:

```text
AssertionError: RAG-008 guarded retrieval policy module is missing.
```

- [ ] **Step 3: Commit validator**

```powershell
git add -- scripts/validate_rag_008_guarded_retrieval_policy.py
git commit -m "test: add RAG-008 guarded retrieval validator" -- scripts/validate_rag_008_guarded_retrieval_policy.py
```

## Task 2: Policy Module

**Files:**
- Create: `scripts/rag_guarded_retrieval_policy.py`

- [ ] **Step 1: Implement minimal policy builder**

Expose:

- `RAG_GUARDED_RETRIEVAL_POLICY_ID = "RAG-008-guarded-retrieval-policy"`
- `build_guarded_retrieval_policy(rag007_path, case_path, *, root=None) -> dict`
- `render_guarded_retrieval_policy_report(payload) -> str`

The builder must:

- reject `data/private` and `data/private-restricted` input paths
- require `reviewed_slice_id == "RAG-007-reviewed-first-slice"`
- load `knowledge_items`
- reject items that are not manually reviewed paraphrases
- reject any item with `runtime_eligible_now: true` or `retrieval_eligible_now: true`
- block hard context flags before matching
- match by deterministic keyword overlap against `query`, `project_rule`, `safe_application`, `do_not_use_when`, and `guardrail_notes`
- obey `lane_filter`
- return at most `max_results` candidates
- emit candidate packets with source IDs and no source excerpt text

- [ ] **Step 2: Run validator to verify GREEN for module contract**

Run:

```powershell
python scripts\validate_rag_008_guarded_retrieval_policy.py
```

Expected next failure:

```text
AssertionError: RAG-008 guarded retrieval policy runner is missing.
```

- [ ] **Step 3: Commit module**

```powershell
git add -- scripts/rag_guarded_retrieval_policy.py
git commit -m "feat: add RAG-008 guarded retrieval policy builder" -- scripts/rag_guarded_retrieval_policy.py
```

## Task 3: Runner, Case File, and Product Doc

**Files:**
- Create: `scripts/run_rag_008_guarded_retrieval_policy.py`
- Create: `research/experiments/cases/rag-008-guarded-retrieval-policy.json`
- Create: `docs/product/RAG_008_GUARDED_RETRIEVAL_POLICY.md`

- [ ] **Step 1: Add runner**

The runner must default to:

- RAG-007 input: `research/experiments/generated/RAG-007-reviewed-first-slice/result.json`
- case file: `research/experiments/cases/rag-008-guarded-retrieval-policy.json`
- output folder: `research/experiments/generated/RAG-008-guarded-retrieval-policy`

The runner must reject inputs and outputs outside the repo root and under private paths.

- [ ] **Step 2: Add official case file**

Include synthetic cases:

- `ordinary_objection_yes_and`
- `broad_question_structure`
- `tone_uncertainty_clarification`
- `customer_refusal_blocks`
- `protected_script_blocks`
- `human_escalation_blocks`
- `pressure_sensitive_blocks`
- `private_data_request_blocks`

- [ ] **Step 3: Add product doc**

Document purpose, commands, default output, dry-run-only boundary, blocking rules, and non-runtime status.

- [ ] **Step 4: Run validator**

Run:

```powershell
python scripts\validate_rag_008_guarded_retrieval_policy.py
```

Expected result:

```text
RAG-008 guarded retrieval policy validation passed.
```

- [ ] **Step 5: Commit runner/case/doc**

```powershell
git add -- scripts/run_rag_008_guarded_retrieval_policy.py research/experiments/cases/rag-008-guarded-retrieval-policy.json docs/product/RAG_008_GUARDED_RETRIEVAL_POLICY.md
git commit -m "feat: add RAG-008 guarded retrieval runner" -- scripts/run_rag_008_guarded_retrieval_policy.py research/experiments/cases/rag-008-guarded-retrieval-policy.json docs/product/RAG_008_GUARDED_RETRIEVAL_POLICY.md
```

## Task 4: Generate Official RAG-008 Artifacts

**Files:**
- Create: `research/experiments/generated/RAG-008-guarded-retrieval-policy/result.json`
- Create: `research/experiments/generated/RAG-008-guarded-retrieval-policy/report.md`

- [ ] **Step 1: Run official generator**

```powershell
python scripts\run_rag_008_guarded_retrieval_policy.py
```

Expected summary:

- `query_case_count: 8`
- `retrieval_case_count: 3`
- `blocked_case_count: 5`
- runtime and chunk import flags all false

- [ ] **Step 2: Validate official artifact**

```powershell
python scripts\validate_rag_008_guarded_retrieval_policy.py
```

- [ ] **Step 3: Commit generated artifacts**

```powershell
git add -- research/experiments/generated/RAG-008-guarded-retrieval-policy/result.json research/experiments/generated/RAG-008-guarded-retrieval-policy/report.md
git commit -m "data: generate RAG-008 guarded retrieval packet" -- research/experiments/generated/RAG-008-guarded-retrieval-policy/result.json research/experiments/generated/RAG-008-guarded-retrieval-policy/report.md
```

## Task 5: Docs, Setup, and Thesis Wiring

**Files:**
- Modify: `docs/product/COMMANDS.md`
- Modify: `scripts/check_setup.py`
- Modify: `docs/thesis/ROADMAP.md`
- Modify: `docs/thesis/METHODOLOGY_LOG.md`

- [ ] **Step 1: Add COMMANDS section**

Add RAG-008 after RAG-007 with run, output folder, and validation commands.

- [ ] **Step 2: Add setup checks**

Add required checks for:

- `docs/product/RAG_008_GUARDED_RETRIEVAL_POLICY.md`
- `scripts/rag_guarded_retrieval_policy.py`
- `scripts/run_rag_008_guarded_retrieval_policy.py`
- `scripts/validate_rag_008_guarded_retrieval_policy.py`
- `research/experiments/cases/rag-008-guarded-retrieval-policy.json`

- [ ] **Step 3: Update thesis docs**

Roadmap:

- mark RAG-008 complete
- next checkpoint should remain validation-first before runtime retrieval

Methodology log:

- record objective, data used, output created, learned boundaries, and open questions

- [ ] **Step 4: Validate setup**

```powershell
python scripts\validate_rag_008_guarded_retrieval_policy.py
python scripts\check_setup.py
```

- [ ] **Step 5: Commit wiring**

```powershell
git add -- docs/product/COMMANDS.md scripts/check_setup.py docs/thesis/ROADMAP.md docs/thesis/METHODOLOGY_LOG.md
git commit -m "docs: document RAG-008 guarded retrieval policy" -- docs/product/COMMANDS.md scripts/check_setup.py docs/thesis/ROADMAP.md docs/thesis/METHODOLOGY_LOG.md
```

## Final Verification

Run:

```powershell
python scripts\validate_rag_004_source_manifest_normalization.py
python scripts\validate_rag_005_chunk_normalization.py
python scripts\validate_rag_006_chunk_review_packet.py
python scripts\validate_rag_007_reviewed_first_slice.py
python scripts\validate_rag_008_guarded_retrieval_policy.py
python scripts\check_setup.py
git diff --check
```

Run fixed-string boundary scans:

```powershell
rg -n -F '"runtime_retrieval_enabled": true' scripts docs\product research\experiments\cases research\experiments\generated\RAG-008-guarded-retrieval-policy
rg -n -F '"retrieval_used_in_runtime": true' scripts docs\product research\experiments\cases research\experiments\generated\RAG-008-guarded-retrieval-policy
rg -n -F '"chunk_import_enabled": true' scripts docs\product research\experiments\cases research\experiments\generated\RAG-008-guarded-retrieval-policy
rg -n -F '"source_excerpt_text":' research\experiments\generated\RAG-008-guarded-retrieval-policy docs\product\RAG_008_GUARDED_RETRIEVAL_POLICY.md
```

All scans should return no matches.
