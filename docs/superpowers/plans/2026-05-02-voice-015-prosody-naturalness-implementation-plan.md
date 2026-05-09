# VOICE-015 Prosody Naturalness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a provider-neutral prosody cue layer that adds professional-human pause, rate, emphasis, pitch, and rare stretch cues without modifying protected campaign or compliance text.

**Architecture:** Add a focused prosody planner alongside the existing VOICE-012 speech naturalness renderer. The planner emits clean TTS text, review-only debug text, and structured cues that future provider adapters can translate safely.

**Tech Stack:** Python standard library, JSON case files, Markdown reports, existing project validator pattern.

---

### Task 1: Validator First

**Files:**
- Create: `scripts/validate_voice_015_prosody_naturalness.py`

- [x] **Step 1: Write the failing validator**

Create a validator that expects a VOICE-015 runner, case file, deterministic generated JSON, bounded cue ranges, and zero cues inside protected segments.

- [x] **Step 2: Run validator to verify RED**

Run:

```powershell
python scripts\validate_voice_015_prosody_naturalness.py
```

Expected:

```text
AssertionError: VOICE-015 runner is missing.
```

### Task 2: Prosody Planner And Cases

**Files:**
- Create: `scripts/prosody_naturalness.py`
- Create: `scripts/run_voice_015_prosody_naturalness.py`
- Create: `research/experiments/cases/voice-015-prosody-naturalness.json`

- [x] **Step 1: Implement provider-neutral cue planning**

Create `apply_prosody_naturalness()` that returns `tts_text`, `debug_text`, `prosody_plan`, cue counts, validation, and runtime boundaries.

- [x] **Step 2: Add bilingual cases**

Cover English and German freeform speech, protected questions, disclosures, do-not-call, hangup, strict insurance boundaries, and disabled clean-script mode.

- [x] **Step 3: Verify GREEN**

Run:

```powershell
python scripts\validate_voice_015_prosody_naturalness.py
```

Expected:

```text
VOICE-015 prosody naturalness validation passed.
```

### Task 3: Generated Artifacts And Documentation

**Files:**
- Create: `research/experiments/generated/VOICE-015/VOICE-015-prosody-naturalness.json`
- Create: `research/experiments/generated/VOICE-015/VOICE-015-prosody-naturalness-report.md`
- Create: `docs/product/VOICE_015_PROSODY_NATURALNESS_LAYER.md`
- Create: `research/experiments/VOICE-015-prosody-naturalness.md`
- Modify: `docs/product/COMMANDS.md`
- Modify: `scripts/check_setup.py`
- Modify: `docs/thesis/METHODOLOGY_LOG.md`
- Modify: `docs/thesis/ROADMAP.md`

- [x] **Step 1: Generate artifacts**

Run:

```powershell
python scripts\run_voice_015_prosody_naturalness.py
```

- [x] **Step 2: Document behavior and thesis meaning**

Record the cue boundary, provider-neutral rendering rule, seeded randomization, protected segment lock, and next provider-rendering checkpoint.

### Task 4: Verification

**Files:**
- Validate all touched voice checkpoints.

- [x] **Step 1: Run validators**

Run:

```powershell
python scripts\validate_voice_015_prosody_naturalness.py
python scripts\validate_voice_014_provider_listening_comparison.py
python scripts\validate_voice_013_elevenlabs_tts_smoke.py
python scripts\validate_voice_012_speech_naturalness.py
python scripts\validate_voice_011_cartesia_websocket_smoke.py
python scripts\validate_check_setup.py
python scripts\check_setup.py --json
```

- [x] **Step 2: Run secret scan**

Scan project text files for provider keys and bearer-token patterns, excluding ignored generated audio and public datasets.
