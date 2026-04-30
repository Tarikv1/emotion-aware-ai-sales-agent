# VOICE-004 Browser Speech Recognition Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a no-key browser speech recognition demo that sends transcript text to the existing realtime sales-agent core and speaks back the selected response.

**Architecture:** `scripts/run_browser_speech_demo.py` renders a browser demo and can also run a local HTTP server. The browser handles microphone permission and speech recognition, then posts transcript text to `/decide`; Python routes that transcript through the realtime agent and returns a VOICE-004 packet with a VOICE-001 response packet.

**Tech Stack:** Python standard library `http.server`, existing realtime turn modules, existing VOICE-001 packet helper, browser Web Speech API, generated HTML/JSON artifacts.

---

## File Structure

- Create: `scripts/run_browser_speech_demo.py`
  - Serves and exports the browser speech demo, metadata, and decision packets.
- Create: `scripts/validate_voice_004_browser_speech_demo.py`
  - Validates exports, decision mode, consent disclosure, and secret-safe output.
- Create: `docs/product/VOICE_004_BROWSER_SPEECH_DEMO.md`
  - Documents the browser speech recognition demo and local-server contract.
- Create: `research/experiments/VOICE-004-browser-speech-demo.md`
  - Records the experiment setup and interpretation.
- Generate: `research/experiments/generated/VOICE-004-browser-speech-demo.html`
  - Browser demo page.
- Generate: `research/experiments/generated/VOICE-004-browser-speech-demo-metadata.json`
  - Demo metadata.
- Generate: `research/experiments/generated/VOICE-004-browser-speech-demo-decision.json`
  - Deterministic sample decision.

## Task 1: Add Failing Validator

**Files:**
- Create: `scripts/validate_voice_004_browser_speech_demo.py`

- [ ] **Step 1: Write validator before implementation**

The validator should run export mode and decision mode, then assert Web Speech API usage, consent gating, local transcript routing, and claim-boundary escalation.

- [ ] **Step 2: Run validator to verify it fails**

Run:

```powershell
python scripts\validate_voice_004_browser_speech_demo.py
```

Expected: fail because `scripts/run_browser_speech_demo.py` is missing.

## Task 2: Implement Browser Demo Script

**Files:**
- Create: `scripts/run_browser_speech_demo.py`

- [ ] **Step 1: Implement metadata and decision packet builders**

Reuse:

- `realtime_turn_cli.build_turn_case`
- `realtime_turn_cli.find_campaign`
- `realtime_turn_cli.run_turn_decision`
- `generate_voice_response.build_voice_packet`

- [ ] **Step 2: Implement HTML renderer**

The page should include:

- consent checkbox
- `SpeechRecognition` / `webkitSpeechRecognition`
- start listening button
- sample transcript button
- call to local `/decide`
- browser speech synthesis playback

- [ ] **Step 3: Implement local HTTP server**

Expose:

- `GET /`
- `GET /metadata`
- `POST /decide`

- [ ] **Step 4: Implement export and decision CLI modes**

Support:

- `--export-html`
- `--export-metadata`
- `--decision-transcript`
- `--decision-out`
- serving mode when no export/decision mode is provided

## Task 3: Generate Artifacts And Docs

**Files:**
- Create: `docs/product/VOICE_004_BROWSER_SPEECH_DEMO.md`
- Create: `research/experiments/VOICE-004-browser-speech-demo.md`
- Generate: `research/experiments/generated/VOICE-004-browser-speech-demo.html`
- Generate: `research/experiments/generated/VOICE-004-browser-speech-demo-metadata.json`
- Generate: `research/experiments/generated/VOICE-004-browser-speech-demo-decision.json`

## Task 4: Verify, Commit, And Push

Run:

```powershell
python scripts\validate_voice_004_browser_speech_demo.py
python scripts\validate_voice_003_asr_provider_comparison.py
python scripts\validate_voice_002_audio_input.py
python scripts\validate_voice_001_tts.py
python scripts\validate_realtime_turn_cli.py
```

Commit message:

```text
Add VOICE-004 browser speech demo
```

