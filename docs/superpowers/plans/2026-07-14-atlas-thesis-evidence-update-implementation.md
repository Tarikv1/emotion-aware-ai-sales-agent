# Atlas Thesis Evidence Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update thesis documentation and traceability so it accurately reflects the completed Atlas 019-040 evidence and its limitations.

**Architecture:** Keep stable historical thesis definitions intact and update only current-state, methodology, decision, evaluation, outline, and source-registry surfaces. Generated `THESIS-DOCS-UPDATE-002` evidence records the exact baseline, claims, limitations, side-effect boundary, and validation results.

**Tech Stack:** Markdown, JSON, Python repository validators, Git.

## Global Constraints

- Do not edit runtime, prompt, KB, dashboard test definitions, Analysis, Procedures, or live provider state.
- Do not run simulations, outbound calls, provider writes, model inference, or audio generation.
- Preserve the historical phase-one baseline and distinguish it from the current Atlas runtime baseline.
- Do not describe full 036/040 suites as universally green; record targeted independent passes and historical full-suite failures honestly.
- Scope readiness to covered hosted Atlas text/simulation behavior; exclude PSTN audio, ASR, latency, interruptions, real buyers, and conversion impact.
- Register existing market/sales URLs as product-context sources, not academic proof or exact pricing authority.
- Use ASCII unless an edited file already requires otherwise.

---

### Task 1: Update Current Thesis Status

**Files:**
- Modify: `docs/thesis/ROADMAP.md`
- Modify: `docs/thesis/PROJECT_BRIEF.md`
- Modify: `docs/thesis/BASELINE_SPEC.md`

**Interfaces:**
- Consumes: final 036/039/040 reports and live structural readback.
- Produces: one consistent current-state and readiness boundary for the remaining thesis documents.

- [ ] Replace the stale roadmap current checkpoint with Atlas 019-040 thesis consolidation and explicit future PSTN/ASR/latency/real-buyer gaps.
- [ ] Update the project brief status without changing the global non-production boundary.
- [ ] Update the runtime baseline addendum with current Atlas pricing, terminal-state, KB, Analysis, tool, and Procedure facts.
- [ ] Run `git diff --check -- docs/thesis/ROADMAP.md docs/thesis/PROJECT_BRIEF.md docs/thesis/BASELINE_SPEC.md`.

### Task 2: Update Methodology, Decisions, Evaluation, And Outline

**Files:**
- Modify: `docs/thesis/METHODOLOGY_LOG.md`
- Modify: `docs/thesis/DECISION_LOG.md`
- Modify: `docs/thesis/PROMPT_EVAL_WORKFLOW.md`
- Modify: `docs/thesis/EVALUATION_RUBRIC.md`
- Modify: `docs/thesis/THESIS_OUTLINE.md`

**Interfaces:**
- Consumes: Task 1 readiness boundary and final trace evidence.
- Produces: thesis-ready research method, decision rationale, evaluation dimensions, and chapter evidence map.

- [ ] Prepend one consolidated 2026-07-14 Atlas 019-040 methodology entry.
- [ ] Add accepted decisions for independent transcript adjudication and buyer-triggered pricing/state-lane control.
- [ ] Add the provider trace-reconciliation workflow: classify product defect, evaluator defect, test-contract defect, or incomplete simulation; fix product only for real product defects; rerun focused cases first.
- [ ] Add rubric dimensions for price intent, atomic tool-bound termination, state continuity, evaluator conflict, and credit-aware evidence collection.
- [ ] Add 036/039/040 evidence paths and limitations to the thesis outline.
- [ ] Run `git diff --check` on the five files.

### Task 3: Repair Thesis Source Traceability

**Files:**
- Modify: `docs/thesis/THESIS_REFERENCE_REGISTRY.md`

**Interfaces:**
- Consumes: the eight URLs reported by `check_thesis_reference_registry.py`.
- Produces: complete source-role classification for existing sales/pricing context references.

- [ ] Register Salesforce, HubSpot, and Bain as sales-practice/product-context sources.
- [ ] Register Upwork, Forbes Advisor, Bark, and Clutch pricing pages as market-context inputs only.
- [ ] State that these sources do not establish academic effectiveness, exact Atlas prices, or measured outcomes.
- [ ] Run `python scripts\check_thesis_reference_registry.py` and `python scripts\validate_thesis_reference_registry.py`.

### Task 4: Create The Thesis Update Evidence Packet

**Files:**
- Create: `research/experiments/generated/THESIS-DOCS-UPDATE-002/report.md`
- Create: `research/experiments/generated/THESIS-DOCS-UPDATE-002/result.json`

**Interfaces:**
- Consumes: final diffs and validator output from Tasks 1-3.
- Produces: durable, sanitized documentation-update evidence.

- [ ] Record baseline `7ad0a1a`, reviewed range through the final branch source, updated and intentionally unchanged thesis files, evidence claims, limitations, and zero-side-effect boundaries.
- [ ] Record the exact validation commands and results.
- [ ] Parse `result.json` with Python and run `git diff --check`.

### Task 5: Final Validation And Commit

**Files:**
- Verify all files from Tasks 1-4.

**Interfaces:**
- Consumes: completed documentation and evidence packet.
- Produces: one clean committed thesis checkpoint.

- [ ] Run both thesis reference commands, both thesis update-gate commands, runtime-manifest validation, project drift guard, and `git diff --check`.
- [ ] Run the explicit `7ad0a1a..HEAD` thesis update-gate check.
- [ ] Review the full diff for overclaims, stale dates, unsupported green claims, private data, and accidental runtime changes.
- [ ] Commit the completed thesis checkpoint.

