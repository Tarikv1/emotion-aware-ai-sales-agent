# VOICE-017 Live A/B Audio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a guarded live-capable A/B audio harness comparing plain guarded text against VOICE-016 prosody-shaped text.

**Architecture:** Add a VOICE-017 runner that reads VOICE-016 provider-rendered inputs, prepares plain/prosody variants per provider, defaults to dry-run, and only calls providers with explicit `--live` plus environment-only keys.

**Tech Stack:** Python standard library, Cartesia WebSocket path, ElevenLabs HTTP streaming path, JSON artifacts, Markdown reports.

---

### Task 1: Validator First

**Files:**
- Create: `scripts/validate_voice_017_live_ab_audio.py`

- [x] **Step 1: Write failing validator**

The validator expects a VOICE-017 runner, case file, deterministic dry-run, forced-missing-key live fallback for both providers, redacted request previews, and no quality claims.

- [x] **Step 2: Run validator to verify RED**

Run:

```powershell
python scripts\validate_voice_017_live_ab_audio.py
```

Expected:

```text
AssertionError: VOICE-017 runner is missing.
```

### Task 2: Runner And Case Config

**Files:**
- Create: `scripts/run_voice_017_live_ab_audio.py`
- Create: `research/experiments/cases/voice-017-live-ab-audio.json`
- Modify: `.gitignore`

- [x] **Step 1: Implement dry-run and live-capable provider paths**

Support dry-run, forced-missing-key fallback, ElevenLabs live streaming, and Cartesia WebSocket live streaming.

- [x] **Step 2: Ignore generated live audio**

Ignore:

```text
research/experiments/generated/VOICE-017-*.mp3
research/experiments/generated/VOICE-017-*.wav
```

- [x] **Step 3: Run validator to verify GREEN**

Run:

```powershell
python scripts\validate_voice_017_live_ab_audio.py
```

Expected:

```text
VOICE-017 live A/B audio validation passed.
```

### Task 3: Generated Artifacts And Docs

**Files:**
- Create: `research/experiments/generated/VOICE-017-live-ab-audio.json`
- Create: `research/experiments/generated/VOICE-017-live-ab-audio-report.md`
- Create: `docs/product/VOICE_017_LIVE_AB_AUDIO.md`
- Create: `research/experiments/VOICE-017-live-ab-audio.md`
- Modify: `docs/product/COMMANDS.md`
- Modify: `scripts/check_setup.py`
- Modify: `docs/thesis/METHODOLOGY_LOG.md`
- Modify: `docs/thesis/ROADMAP.md`

- [x] **Step 1: Generate official dry-run artifacts**

Run:

```powershell
python scripts\run_voice_017_live_ab_audio.py
```

- [x] **Step 2: Run final verification and secret scan**

Run VOICE-011 through VOICE-017 validators, setup checks, syntax checks, `git diff --check`, and a repository secret scan.
