# VOICE-028 Controlled Delivery Imperfections

## Purpose

VOICE-028 adds a small, controlled imperfection layer for eligible freeform voice delivery.

The goal is not to make the agent sound messy. The goal is to reduce machine-perfect delivery by adding rare, professional human-like rephrases at safe thought boundaries.

## Design Rule

Controlled imperfections are:

- opt-in by campaign through `speech_imperfections.enabled`
- limited to one imperfection per response by default
- language-aware for English and German
- blocked for protected campaign text
- blocked for unsafe claim contexts, stop intent, anger, and handoff-like states
- offline by default, with no TTS provider call and no customer audio upload

Examples:

- English safe freeform: `I can keep this simple. Actually, the useful thing is...`
- German safe freeform: `Ich halte es kurz. Genauer gesagt, wir klaeren nur...`

Protected lines remain exact, including campaign questions, required disclosures, appointment confirmations, handoff scripts, and hangup lines.

## Runtime Position

```text
RESP-001 guarded response
  -> spoken text normalization
  -> speech realism
  -> interaction prosody
  -> controlled imperfections
  -> provider-neutral prosody
  -> provider preview / live TTS boundary
```

The guarded `final_response` is never changed. VOICE-028 only changes provider-facing TTS text for eligible freeform speech.

## Files

- `scripts/speech_imperfections.py`
- `scripts/run_voice_028_controlled_imperfections.py`
- `scripts/validate_voice_028_controlled_imperfections.py`
- `research/experiments/cases/voice-028-controlled-imperfections.json`
- `research/experiments/generated/VOICE-028-controlled-imperfections/results.json`
- `research/experiments/generated/VOICE-028-controlled-imperfections/report.md`

## Commands

Run the offline checkpoint:

```powershell
python scripts\run_voice_028_controlled_imperfections.py
```

Validate the checkpoint:

```powershell
python scripts\validate_voice_028_controlled_imperfections.py
```

## Current Result

The offline checkpoint covers five synthetic cases:

- English safe freeform
- German safe freeform
- German protected campaign question
- English unsafe-claim suppression
- English stop-intent suppression

Expected guard result:

```text
cases: 5
languages: English and German
imperfections: 2
protected segment changes: 0
unsafe visible imperfections: 0
provider calls made: false
customer audio uploaded: false
voice cloning used: false
```

## Thesis Value

VOICE-028 records a bounded response to listening feedback that AI voice output can sound too perfect. It creates a testable layer for professional delivery imperfections while preserving campaign safety, bilingual behavior, and vertical-agnostic architecture.

The next evaluation should use live audio only after the offline validator passes, then compare whether controlled imperfections increase perceived human-likeness without reducing clarity, trust, or sales professionalism.
