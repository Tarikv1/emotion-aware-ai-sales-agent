# RESP-004 VOICE-044 Listening Check

## Purpose

RESP-004 is a separate listening-check checkpoint for the VOICE-044 polished baseline.

It does not replace, rename, or overwrite RESP-003. RESP-003 remains the runtime live-capable TTS bridge. RESP-004 owns the new test scope, evidence folder, and listening-review gate.

## Layer Position

```text
RESP-001 guarded response
  -> RESP-002 runtime voice delivery
  -> VOICE-044 baseline delivery polish
  -> RESP-003 runtime live-capable TTS bridge
  -> RESP-004 short listening-check evidence
```

## Default Test Set

Default RESP-004 uses the first two official VOICE-044 synthetic focus cases:

- English fast-filler cleanup, checking the VOICE-044 phrase-flow polish around `I'll keep this practical. You're right to ask.`
- German connector cleanup, checking the VOICE-044 connector cleanup around `also wenn's`

These cases target the artifacts that motivated VOICE-044. Broader campaign coverage belongs to a later checkpoint.

## Boundary

- Dry-run by default.
- No provider call unless `--live` is passed.
- No API key required in default mode.
- No raw private audio read.
- No customer audio upload.
- No transcription.
- No voice cloning.
- No API key or raw voice ID logging.
- No quality claim before Tarik records a human listening review.

## Commands

Run the dry-run check:

```powershell
python scripts\run_resp_004_voice_044_listening_check.py
```

Validate the dry-run, forced missing-key fallback, RESP-004 artifact shape, and secret redaction:

```powershell
python scripts\validate_resp_004_voice_044_listening_check.py
```

Default output folder:

```text
research\experiments\generated\RESP-004-voice-044-listening-check\
```

Live provider execution remains explicit:

```powershell
python scripts\run_resp_004_voice_044_listening_check.py --provider elevenlabs --live --timeout-seconds 8
```

Use live mode only after the local provider boundary review. Generated audio must stay under the RESP-004 output folder and requires human listening review before any quality claim.
