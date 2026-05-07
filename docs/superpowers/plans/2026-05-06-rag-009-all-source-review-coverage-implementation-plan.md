# RAG-009 All-Source Review Coverage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build RAG-009 as an offline all-source review coverage gate that accounts for every RAG-004 source and every RAG-005 chunk before any runtime retrieval work.

**Architecture:** Add one deterministic Python builder that reads RAG-004, RAG-005, RAG-006, and RAG-007 artifacts, then emits source coverage, chunk coverage, review queues, a promotion ledger, and bounded next-promotion candidates. Add a CLI runner, synthetic/contract case config, product docs, generated artifacts, and setup/thesis wiring. Runtime retrieval, chunk import, embeddings, vector DBs, provider calls, NotebookLM calls, and private reads stay disabled.

**Tech Stack:** Python standard library, JSON artifacts, Markdown reports, existing project `scripts/check_setup.py`, existing RAG artifact conventions.

---

### Task 1: Validator Contract

**Files:**
- Create: `scripts/validate_rag_009_all_source_review_coverage.py`

- [ ] **Step 1: Write the failing validator**

Create `scripts/validate_rag_009_all_source_review_coverage.py` with this contract shape:

```python
#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "rag_all_source_review_coverage.py"
RUNNER = ROOT / "scripts" / "run_rag_009_all_source_review_coverage.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "rag-009-all-source-review-coverage.json"
DOC_PATH = ROOT / "docs" / "product" / "RAG_009_ALL_SOURCE_REVIEW_COVERAGE.md"
TMP_DIR = ROOT / ".tmp" / "rag-009-validation"
EXPECTED_ID = "RAG-009-all-source-review-coverage"

def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)

def write_fixture_inputs() -> dict[str, Path]:
    shutil.rmtree(TMP_DIR, ignore_errors=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    source_manifest = {
        "source_manifest_id": "RAG-004-source-manifest-normalization",
        "summary": {"source_count": 4, "runtime_retrieval_enabled": False},
        "source_manifest": {"sources": [
            {"source_id": "rag004-source-001", "canonical_title": "Mapped voice source", "metadata_status": "needs_human_review", "rights_status": "needs_review", "topic_ids": ["speech_tone_prosody_human_like_voice_behavior"], "raw_source_text_stored": False, "secret_like_detected": False},
            {"source_id": "rag004-source-002", "canonical_title": "Mapped objection source", "metadata_status": "needs_human_review", "rights_status": "needs_review", "topic_ids": ["objection_handling"], "raw_source_text_stored": False, "secret_like_detected": False},
            {"source_id": "rag004-source-003", "canonical_title": "Mapped compliance-risk source", "metadata_status": "needs_human_review", "rights_status": "needs_review", "topic_ids": ["ethical_persuasion_persuasive_dialogue"], "raw_source_text_stored": False, "secret_like_detected": False},
            {"source_id": "rag004-source-004", "canonical_title": "Unused but accounted source", "metadata_status": "needs_human_review", "rights_status": "needs_review", "topic_ids": ["cold_calling"], "raw_source_text_stored": False, "secret_like_detected": False},
        ]},
    }
    chunk_candidates = [
        chunk("rag005-chunk-001", "Mapped voice source", ["rag004-source-001"], ["speech_tone_prosody_human_like_voice_behavior"], [], False, "Bounded vocal clarity", "Use delivery cues as advisory metadata.", "voice_delivery"),
        chunk("rag005-chunk-002", "Mapped objection source", ["rag004-source-002"], ["objection_handling"], ["quote_review_required"], True, "Objection acknowledgement", "Acknowledge normal objections without pressure.", "response_wording"),
        chunk("rag005-chunk-003", "Unknown source", [], ["cold_calling"], ["source_mapping_required"], False, "Needs source mapping", "Blocked until a source is mapped.", "response_wording"),
        chunk("rag005-chunk-004", "Mapped objection source", ["rag004-source-002"], ["off_taxonomy"], ["topic_mapping_required"], False, "Needs topic mapping", "Blocked until topic mapping is reviewed.", "response_wording"),
        chunk("rag005-chunk-005", "Mapped compliance-risk source", ["rag004-source-003"], ["ethical_persuasion_persuasive_dialogue"], [], False, "False certainty claim", "Infer the customer's hidden emotion with certainty.", "emotion_detection"),
        chunk("rag005-chunk-006", "Mapped compliance-risk source", ["rag004-source-003"], ["ethical_persuasion_persuasive_dialogue"], [], False, "Pressure tactic", "Create urgency to push past hesitation.", "response_wording"),
    ]
    rag005 = {"chunk_normalization_id": "RAG-005-chunk-normalization", "summary": {"chunk_candidate_count": len(chunk_candidates), "runtime_retrieval_enabled": False, "chunk_import_enabled": False, "source_excerpt_text_stored": False}, "chunk_candidates": chunk_candidates}
    rag006 = {
        "review_packet_id": "RAG-006-chunk-review-packet",
        "summary": {"chunk_candidate_count": len(chunk_candidates), "auto_promoted_chunk_count": 0, "runtime_retrieval_enabled": False, "chunk_import_enabled": False},
        "review_queues": {
            "source_mapping_queue": [{"source_title": "Unknown source", "chunk_ids": ["rag005-chunk-003"], "chunk_count": 1}],
            "topic_mapping_queue": [{"chunk_id": "rag005-chunk-004"}],
            "quote_review_queue": [{"chunk_id": "rag005-chunk-002", "source_excerpt_present": True}],
        },
        "first_slice_candidates": [{"chunk_id": "rag005-chunk-001"}],
    }
    rag007 = {
        "reviewed_slice_id": "RAG-007-reviewed-first-slice",
        "summary": {"knowledge_item_count": 1, "runtime_retrieval_enabled": False, "retrieval_eligible_now": False, "chunk_import_enabled": False},
        "knowledge_items": [{"knowledge_id": "rag007-voice-bounded-vocal-toolbox", "lane": "voice_delivery", "source_chunk_ids": ["rag005-chunk-001"], "source_ids": ["rag004-source-001"], "review_verdict": "manual_first_slice_paraphrased", "quote_dependency_resolved": True, "runtime_eligible_now": False, "retrieval_eligible_now": False}],
    }
    case_config = {"review_coverage_id": EXPECTED_ID, "max_next_promotion_candidates": 10, "reject_patterns": ["hidden emotion with certainty", "push past hesitation"], "runtime_retrieval_enabled": False, "chunk_import_enabled": False}
    paths = {
        "rag004": TMP_DIR / "rag004.json",
        "rag005": TMP_DIR / "rag005.json",
        "rag006": TMP_DIR / "rag006.json",
        "rag007": TMP_DIR / "rag007.json",
        "case": TMP_DIR / "case.json",
        "result": TMP_DIR / "result.json",
        "report": TMP_DIR / "report.md",
    }
    for key, payload in {"rag004": source_manifest, "rag005": rag005, "rag006": rag006, "rag007": rag007, "case": case_config}.items():
        paths[key].write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return paths
```

Also define `chunk()`, `validate_payload()`, `validate_module_contract()`, `validate_runner_contract()`, and `main()` so the validator requires:

- `RAG_ALL_SOURCE_REVIEW_COVERAGE_ID == "RAG-009-all-source-review-coverage"`.
- `build_all_source_review_coverage(rag004_path, rag005_path, rag006_path, rag007_path, case_path, root=ROOT)`.
- `render_all_source_review_coverage_report(payload)`.
- Summary counts: source count `4`, chunk count `6`, reviewed chunks `1`, blocked source-mapping `1`, blocked topic-mapping `1`, blocked quote-clearance `1`, rejected chunks `2`, next candidates `0`.
- `all_rag004_sources_accounted_for` and `all_rag005_chunks_accounted_for` are `true`.
- No output contains source excerpt text, `data/private`, or a runtime-enabled flag.

- [ ] **Step 2: Run validator to verify RED**

Run:

```powershell
python scripts\validate_rag_009_all_source_review_coverage.py
```

Expected: failure with `RAG-009 all-source review coverage module is missing.`

- [ ] **Step 3: Commit validator**

```powershell
git add -- scripts\validate_rag_009_all_source_review_coverage.py
git commit -m "test: add RAG-009 all-source review validator" -- scripts\validate_rag_009_all_source_review_coverage.py
```

### Task 2: Coverage Builder

**Files:**
- Create: `scripts/rag_all_source_review_coverage.py`
- Test: `scripts/validate_rag_009_all_source_review_coverage.py`

- [ ] **Step 1: Implement minimal builder**

Create `scripts/rag_all_source_review_coverage.py` with:

```python
RAG_ALL_SOURCE_REVIEW_COVERAGE_ID = "RAG-009-all-source-review-coverage"
PRIVATE_PATH_PARTS = (("data", "private"), ("data", "private-restricted"))

def build_all_source_review_coverage(rag004_path, rag005_path, rag006_path, rag007_path, case_path, *, root=None) -> dict[str, Any]:
    ...

def render_all_source_review_coverage_report(payload: dict[str, Any]) -> str:
    ...
```

Implementation rules:

- Resolve inputs under project root and reject `data/private` or `data/private-restricted`.
- Load RAG-004 sources from `payload["source_manifest"]["sources"]`.
- Load RAG-005 chunks from `payload["chunk_candidates"]`.
- Load RAG-006 locations from `review_queues` and `first_slice_candidates`.
- Load RAG-007 reviewed chunk IDs from `knowledge_items[*].source_chunk_ids`.
- Build one `source_coverage` row per source ID.
- Build one `chunk_coverage` row per chunk ID.
- Determine chunk status in this order:
  - `reviewed_rag007` if chunk is in RAG-007 reviewed items.
  - `blocked_source_mapping` if no source IDs or `source_mapping_required`.
  - `blocked_topic_mapping` if `topic_mapping_required`.
  - `blocked_quote_clearance` if `quote_review_required` or `source_excerpt_present`.
  - `rejected_safety` if text matches case `reject_patterns`, protected-attribute/false-certainty/compliance risk terms, pressure terms, or private/customer-data terms.
  - `candidate_next_manual_review` otherwise.
- Never copy raw source excerpt fields into the output.
- Include source IDs, topic IDs, review flags, source title, principle/application/when-not-to-use summaries, status, and status reasons.

- [ ] **Step 2: Run validator**

Run:

```powershell
python scripts\validate_rag_009_all_source_review_coverage.py
```

Expected: runner/doc/case missing failure after module contract passes.

- [ ] **Step 3: Commit builder**

```powershell
git add -- scripts\rag_all_source_review_coverage.py
git commit -m "feat: add RAG-009 all-source review builder" -- scripts\rag_all_source_review_coverage.py
```

### Task 3: Runner, Case Config, Product Doc

**Files:**
- Create: `scripts/run_rag_009_all_source_review_coverage.py`
- Create: `research/experiments/cases/rag-009-all-source-review-coverage.json`
- Create: `docs/product/RAG_009_ALL_SOURCE_REVIEW_COVERAGE.md`
- Test: `scripts/validate_rag_009_all_source_review_coverage.py`

- [ ] **Step 1: Add runner**

Implement a CLI runner with defaults:

```python
DEFAULT_RAG004_RESULT = ROOT / "research" / "experiments" / "generated" / "RAG-004-source-manifest-normalization" / "result.json"
DEFAULT_RAG005_RESULT = ROOT / "research" / "experiments" / "generated" / "RAG-005-chunk-normalization" / "result.json"
DEFAULT_RAG006_PACKET = ROOT / "research" / "experiments" / "generated" / "RAG-006-chunk-review-packet" / "result.json"
DEFAULT_RAG007_RESULT = ROOT / "research" / "experiments" / "generated" / "RAG-007-reviewed-first-slice" / "result.json"
DEFAULT_CASE = ROOT / "research" / "experiments" / "cases" / "rag-009-all-source-review-coverage.json"
DEFAULT_OUTPUT_DIR = ROOT / "research" / "experiments" / "generated" / "RAG-009-all-source-review-coverage"
```

Support `--rag004-result`, `--rag005-result`, `--rag006-packet`, `--rag007-result`, `--case`, `--out`, and `--report-out`. Reject input/output paths outside project root and private paths.

- [ ] **Step 2: Add case config**

Create `research/experiments/cases/rag-009-all-source-review-coverage.json` with:

```json
{
  "review_coverage_id": "RAG-009-all-source-review-coverage",
  "title": "All-source RAG review coverage gate",
  "runtime_retrieval_enabled": false,
  "retrieval_used_in_runtime": false,
  "chunk_import_enabled": false,
  "auto_promotion_enabled": false,
  "max_next_promotion_candidates": 25,
  "reject_patterns": [
    "hidden emotion with certainty",
    "guarantee hidden intent",
    "sensitive demographic",
    "protected attribute",
    "rewrite required disclosure",
    "ignore refusal",
    "push past hesitation"
  ],
  "review_lanes": [
    "reviewed_rag007",
    "candidate_next_manual_review",
    "blocked_source_mapping",
    "blocked_topic_mapping",
    "blocked_quote_clearance",
    "rejected_safety",
    "deferred_review"
  ]
}
```

- [ ] **Step 3: Add product doc**

Create `docs/product/RAG_009_ALL_SOURCE_REVIEW_COVERAGE.md` documenting purpose, commands, default output, safety boundary, and readiness meaning. State clearly that RAG-009 covers all sources/chunks but does not enable runtime retrieval.

- [ ] **Step 4: Run validator**

Run:

```powershell
python scripts\validate_rag_009_all_source_review_coverage.py
```

Expected: `RAG-009 all-source review coverage validation passed.`

- [ ] **Step 5: Commit runner/case/doc**

```powershell
git add -- scripts\run_rag_009_all_source_review_coverage.py research\experiments\cases\rag-009-all-source-review-coverage.json docs\product\RAG_009_ALL_SOURCE_REVIEW_COVERAGE.md
git commit -m "feat: add RAG-009 all-source review runner" -- scripts\run_rag_009_all_source_review_coverage.py research\experiments\cases\rag-009-all-source-review-coverage.json docs\product\RAG_009_ALL_SOURCE_REVIEW_COVERAGE.md
```

### Task 4: Official Artifacts

**Files:**
- Create: `research/experiments/generated/RAG-009-all-source-review-coverage/result.json`
- Create: `research/experiments/generated/RAG-009-all-source-review-coverage/report.md`

- [ ] **Step 1: Run official RAG-009**

Run:

```powershell
python scripts\run_rag_009_all_source_review_coverage.py
```

Expected summary includes `source_count: 95`, `chunk_candidate_count: 121`, `all_rag004_sources_accounted_for: true`, `all_rag005_chunks_accounted_for: true`, `runtime_retrieval_enabled: false`, and `chunk_import_enabled: false`.

- [ ] **Step 2: Validate official artifacts**

Run:

```powershell
python scripts\validate_rag_009_all_source_review_coverage.py
```

Expected: `RAG-009 all-source review coverage validation passed.`

- [ ] **Step 3: Commit artifacts**

```powershell
git add -- research\experiments\generated\RAG-009-all-source-review-coverage
git commit -m "test: add RAG-009 all-source review artifacts" -- research\experiments\generated\RAG-009-all-source-review-coverage
```

### Task 5: Command, Setup, Thesis Wiring

**Files:**
- Modify: `docs/product/COMMANDS.md`
- Modify: `scripts/check_setup.py`
- Modify: `docs/thesis/ROADMAP.md`
- Modify: `docs/thesis/METHODOLOGY_LOG.md`

- [ ] **Step 1: Add command map section**

In `docs/product/COMMANDS.md`, after RAG-008 commands, add RAG-009 run/validate commands and default output path.

- [ ] **Step 2: Register setup files**

In `scripts/check_setup.py`, add required-file checks for:

```python
("file.docs_product_rag_009_all_source_review_coverage", "docs/product/RAG_009_ALL_SOURCE_REVIEW_COVERAGE.md", "RAG all-source review coverage")
("file.scripts_rag_all_source_review_coverage", "scripts/rag_all_source_review_coverage.py", "RAG all-source review coverage module")
("file.scripts_run_rag_009_all_source_review_coverage", "scripts/run_rag_009_all_source_review_coverage.py", "RAG all-source review coverage runner")
("file.scripts_validate_rag_009_all_source_review_coverage", "scripts/validate_rag_009_all_source_review_coverage.py", "RAG all-source review coverage validator")
("file.research_case_rag_009_all_source_review_coverage", "research/experiments/cases/rag-009-all-source-review-coverage.json", "RAG all-source review coverage case file")
```

- [ ] **Step 3: Update roadmap and methodology**

In `docs/thesis/ROADMAP.md`, mark RAG-009 completed and set the next RAG checkpoint to a bigger reviewed-slice promotion or runtime-off integration harness. In `docs/thesis/METHODOLOGY_LOG.md`, add a RAG-009 entry with counts from the official artifact and the no-runtime boundary.

- [ ] **Step 4: Validate setup and thesis gates**

Run:

```powershell
python scripts\validate_check_setup.py
python scripts\check_setup.py --json
python scripts\check_thesis_update_gate.py
```

Expected: all pass, with `check_setup.py --json` showing `0` failures.

- [ ] **Step 5: Commit wiring**

```powershell
git add -- docs\product\COMMANDS.md scripts\check_setup.py docs\thesis\ROADMAP.md docs\thesis\METHODOLOGY_LOG.md
git commit -m "docs: document RAG-009 all-source review checkpoint" -- docs\product\COMMANDS.md scripts\check_setup.py docs\thesis\ROADMAP.md docs\thesis\METHODOLOGY_LOG.md
```

### Task 6: Final Verification

**Files:**
- No edits unless verification finds a defect.

- [ ] **Step 1: Run focused RAG chain**

Run:

```powershell
python scripts\validate_rag_007_reviewed_first_slice.py
python scripts\validate_rag_008_guarded_retrieval_policy.py
python scripts\validate_rag_009_all_source_review_coverage.py
```

Expected: all three validations pass.

- [ ] **Step 2: Run project setup gates**

Run:

```powershell
python scripts\validate_check_setup.py
python scripts\check_setup.py --json
python scripts\check_thesis_update_gate.py
```

Expected: all pass, with setup summary reporting `0` failures.

- [ ] **Step 3: Run boundary grep**

Run:

```powershell
rg -n '"runtime_retrieval_enabled": true|"chunk_import_enabled": true|"retrieval_used_in_runtime": true|"runtime_use_allowed": true|"auto_promote_allowed": true|"provider_calls_made": true|"notebooklm_api_used": true|"private_customer_data_used": true|"reads_data_private": true' scripts\rag_all_source_review_coverage.py scripts\run_rag_009_all_source_review_coverage.py docs\product\RAG_009_ALL_SOURCE_REVIEW_COVERAGE.md research\experiments\cases\rag-009-all-source-review-coverage.json research\experiments\generated\RAG-009-all-source-review-coverage
rg -n 'data/private|"source_excerpt_text"\s*:|"source_excerpt"\s*:' docs\product\RAG_009_ALL_SOURCE_REVIEW_COVERAGE.md research\experiments\cases\rag-009-all-source-review-coverage.json research\experiments\generated\RAG-009-all-source-review-coverage
```

Expected: no matches in the RAG-009 surface.

- [ ] **Step 4: Inspect final status**

Run:

```powershell
git status --short -- scripts\rag_all_source_review_coverage.py scripts\run_rag_009_all_source_review_coverage.py scripts\validate_rag_009_all_source_review_coverage.py docs\product\RAG_009_ALL_SOURCE_REVIEW_COVERAGE.md research\experiments\cases\rag-009-all-source-review-coverage.json research\experiments\generated\RAG-009-all-source-review-coverage docs\product\COMMANDS.md scripts\check_setup.py docs\thesis\ROADMAP.md docs\thesis\METHODOLOGY_LOG.md docs\superpowers\plans\2026-05-06-rag-009-all-source-review-coverage-implementation-plan.md
```

Expected: no RAG-009 scoped files are left unstaged or uncommitted.
