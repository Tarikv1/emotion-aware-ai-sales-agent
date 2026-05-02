# VOICE-016 Provider Prosody Rendering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render VOICE-015 provider-neutral prosody cues into offline Cartesia and ElevenLabs provider previews without making live provider calls.

**Architecture:** Add a small provider rendering module that operates per segment. The runner reads the generated VOICE-015 artifact, renders two provider variants per case, writes JSON/Markdown outputs, and validates protected segment boundaries.

**Tech Stack:** Python standard library, JSON artifacts, Markdown reports, existing validator pattern.

---

### Task 1: Validator First

**Files:**
- Create: `scripts/validate_voice_016_provider_prosody_rendering.py`

- [x] **Step 1: Write failing validator**

The validator expects a VOICE-016 runner, case config, deterministic output, two provider variants per case, provider mapping counts, and zero provider tags inside protected segments.

- [x] **Step 2: Run validator to verify RED**

Run:

```powershell
python scripts\validate_voice_016_provider_prosody_rendering.py
```

Expected:

```text
AssertionError: VOICE-016 runner is missing.
```

### Task 2: Renderer And Runner

**Files:**
- Create: `scripts/provider_prosody_rendering.py`
- Create: `scripts/run_voice_016_provider_prosody_rendering.py`
- Create: `research/experiments/cases/voice-016-provider-prosody-rendering.json`

- [x] **Step 1: Implement per-segment provider rendering**

Map Cartesia pause/rate/emphasis/stretch cues to SSML-style tags. Map ElevenLabs pause cues to break tags and rate cues to request-level speed. Record unsupported cues instead of forcing them.

- [x] **Step 2: Run validator to verify GREEN**

Run:

```powershell
python scripts\validate_voice_016_provider_prosody_rendering.py
```

Expected:

```text
VOICE-016 provider prosody rendering validation passed.
```

### Task 3: Generated Artifacts And Docs

**Files:**
- Create: `research/experiments/generated/VOICE-016-provider-prosody-rendering.json`
- Create: `research/experiments/generated/VOICE-016-provider-prosody-rendering-report.md`
- Create: `docs/product/VOICE_016_PROVIDER_PROSODY_RENDERING.md`
- Create: `research/experiments/VOICE-016-provider-prosody-rendering.md`
- Modify: `docs/product/COMMANDS.md`
- Modify: `scripts/check_setup.py`
- Modify: `docs/thesis/METHODOLOGY_LOG.md`
- Modify: `docs/thesis/ROADMAP.md`

- [x] **Step 1: Generate official artifacts**

Run:

```powershell
python scripts\run_voice_016_provider_prosody_rendering.py
```

- [x] **Step 2: Run final verification and secret scan**

Run the VOICE-011 through VOICE-016 validators, setup checks, syntax checks, `git diff --check`, and a repository secret scan.
