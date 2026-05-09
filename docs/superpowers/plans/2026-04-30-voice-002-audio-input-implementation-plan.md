# VOICE-002 Audio Input Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a safe recorded-audio input prototype that pairs an audio file with a transcript, routes the transcript through the realtime sales-agent core, and produces a VOICE-002 packet plus browser listener.

**Architecture:** `scripts/run_voice_input_turn.py` validates audio metadata, uses a `manual-transcript` transcription adapter, calls the existing realtime decision and VOICE-001 packet builder, then writes JSON and optional HTML listener artifacts. The first implementation is provider-safe and does not use cloud ASR.

**Tech Stack:** Python standard library, existing realtime turn modules, existing VOICE-001 packet helpers, JSON artifacts, local HTML listener.

---

## File Structure

- Create: `scripts/validate_voice_002_audio_input.py`
  - Generates a synthetic placeholder WAV fixture, verifies consent gating, runs VOICE-002, and checks packet/listener behavior.
- Create: `scripts/run_voice_input_turn.py`
  - Implements recorded-audio metadata extraction, manual transcript ingestion, realtime-agent routing, VOICE-001 response packet reuse, JSON output, and listener rendering.
- Create: `docs/product/VOICE_002_AUDIO_INPUT_PROTOTYPE.md`
  - Documents the milestone and explains why `manual-transcript` comes before cloud ASR.
- Create: `research/experiments/VOICE-002-audio-input-prototype.md`
  - Records the experiment setup and interpretation.
- Generate: `research/experiments/generated/VOICE-002/VOICE-002-audio-input-packet.json`
  - Stores the deterministic VOICE-002 packet.
- Generate: `research/experiments/generated/VOICE-002/VOICE-002-listen.html`
  - Local browser listener for the resulting agent response.

## Task 1: Add Failing Validator

**Files:**
- Create: `scripts/validate_voice_002_audio_input.py`

- [ ] **Step 1: Write the validator before implementation**

The validator should create a synthetic placeholder WAV, assert the VOICE-002 script exists, verify that consent is required, then run the script with a known transcript.

- [ ] **Step 2: Run validator to verify it fails**

Run:

```powershell
python scripts\validate_voice_002_audio_input.py
```

Expected: fail with `VOICE-002 audio-input script is missing`.

## Task 2: Implement Audio-Input Script

**Files:**
- Create: `scripts/run_voice_input_turn.py`

- [ ] **Step 1: Add CLI and audio metadata extraction**

The script should support:

- `--campaign`
- `--stage`
- `--audio`
- `--transcript`
- `--transcript-file`
- `--provider manual-transcript`
- `--input-type speech-final`
- `--silence-count`
- `--cases`
- `--consent-confirmed`
- `--out-json`
- `--listener-out`

- [ ] **Step 2: Add consent gate**

If `--consent-confirmed` is missing, the script should exit before writing outputs.

- [ ] **Step 3: Route transcript through existing realtime agent**

The script should call the same realtime turn functions used by VOICE-001 and build a VOICE-001-compatible response packet.

- [ ] **Step 4: Add listener rendering**

The listener should show the audio path, transcript, selected agent response, and a browser speech-synthesis play button.

## Task 3: Add Product And Experiment Docs

**Files:**
- Create: `docs/product/VOICE_002_AUDIO_INPUT_PROTOTYPE.md`
- Create: `research/experiments/VOICE-002-audio-input-prototype.md`

- [ ] **Step 1: Document the product role**

Explain that VOICE-002 is an audio-input adapter layer around the reusable sales-agent core.

- [ ] **Step 2: Document the experiment**

Record the synthetic placeholder WAV, manual transcript provider, resulting realtime decision, and safety interpretation.

## Task 4: Verify, Commit, And Push

**Files:**
- Verify all created files and generated artifacts.

- [ ] **Step 1: Run validators**

Run:

```powershell
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
Add VOICE-002 audio input prototype
```

Push `main` to `origin/main`.

