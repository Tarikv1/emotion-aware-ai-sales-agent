# VOICE-003 ASR Provider Comparison Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic ASR provider-family comparison framework that recommends the safest next speech-to-text prototype path without making external API calls.

**Architecture:** A JSON candidate file stores provider-family capabilities and risks. `scripts/compare_asr_providers.py` scores the candidates against product weights, writes JSON results, and renders a Markdown report. A validator checks the comparison contract and secret-safe output.

**Tech Stack:** Python standard library, JSON candidate data, Markdown report artifacts, existing validation script pattern.

---

## File Structure

- Create: `research/experiments/cases/voice-003-asr-provider-candidates.json`
  - Provider-family candidate data and scoring weights.
- Create: `scripts/compare_asr_providers.py`
  - Deterministic scorer and report renderer.
- Create: `scripts/validate_voice_003_asr_provider_comparison.py`
  - Validates provider coverage, recommendation logic, generated artifacts, and secret-safe output.
- Create: `docs/product/VOICE_003_ASR_PROVIDER_COMPARISON.md`
  - Documents the product decision and adapter boundary.
- Create: `research/experiments/VOICE-003-asr-provider-comparison.md`
  - Records the experiment result and interpretation.
- Generate: `research/experiments/generated/VOICE-003/VOICE-003-asr-provider-comparison.json`
  - Stores comparison results.
- Generate: `research/experiments/generated/VOICE-003/VOICE-003-asr-provider-comparison-report.md`
  - Stores the generated report.

## Task 1: Add Failing Validator

**Files:**
- Create: `scripts/validate_voice_003_asr_provider_comparison.py`

- [ ] **Step 1: Write the validator before implementation**

The validator should run `scripts/compare_asr_providers.py` against the provider candidate JSON and check the generated JSON and Markdown report.

- [ ] **Step 2: Run validator to verify it fails**

Run:

```powershell
python scripts\validate_voice_003_asr_provider_comparison.py
```

Expected: fail because the comparison script and candidate file are missing.

## Task 2: Add Candidate Data And Comparison Script

**Files:**
- Create: `research/experiments/cases/voice-003-asr-provider-candidates.json`
- Create: `scripts/compare_asr_providers.py`

- [ ] **Step 1: Add provider-family candidate data**

Include manual transcript, browser speech recognition demo, local/offline ASR, cloud batch ASR, cloud streaming ASR, and hybrid edge/cloud ASR.

- [ ] **Step 2: Add deterministic scoring**

Score candidates using weighted fields for latency, privacy, no-key prototype fit, streaming, batch support, German readiness, integration simplicity, cost control, and thesis usefulness.

- [ ] **Step 3: Render JSON and Markdown outputs**

The report should explicitly state that no API calls were made and no audio was uploaded.

## Task 3: Add Product And Experiment Docs

**Files:**
- Create: `docs/product/VOICE_003_ASR_PROVIDER_COMPARISON.md`
- Create: `research/experiments/VOICE-003-asr-provider-comparison.md`

- [ ] **Step 1: Document product decision**

Explain why provider-family comparison comes before real ASR integration.

- [ ] **Step 2: Document experiment result**

Record the recommended next prototype path and caveats.

## Task 4: Verify, Commit, And Push

**Files:**
- Verify all created files and generated artifacts.

- [ ] **Step 1: Run validators**

Run:

```powershell
python scripts\validate_voice_003_asr_provider_comparison.py
python scripts\validate_voice_002_audio_input.py
python scripts\validate_voice_001_tts.py
python scripts\validate_realtime_turn_cli.py
```

Expected: all commands exit `0`.

- [ ] **Step 2: Run secret scan**

Scan changed files for:

```text
sk-[A-Za-z0-9_-]{20,}|OPENAI_API_KEY\s*=|Authorization:\s*Bearer\s+[A-Za-z0-9]
```

Expected: no matches.

- [ ] **Step 3: Commit and push**

Commit message:

```text
Add VOICE-003 ASR provider comparison
```

Push `main` to `origin/main`.

