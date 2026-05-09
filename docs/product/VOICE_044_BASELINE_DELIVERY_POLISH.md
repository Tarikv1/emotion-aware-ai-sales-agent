# VOICE-044 Baseline Delivery Polish

VOICE-044 improves the accepted baseline shaped runtime directly after VOICE-043.

It does not promote the VOICE-041 private-pattern profile. It only applies narrow provider-facing cleanup to eligible freeform TTS text.

## Decision

- Keep VOICE-043 as the baseline acceptance guard.
- Keep VOICE-041 private-pattern settings disabled by default.
- Remove brittle English trust-style filler joins that can blur in live audio.
- Clean German `also wenn's` connector casing after connected-speech joins.
- Cap only overly long German baseline break tags in the polish layer.
- Leave protected text exactly unchanged.

## Runtime Position

```text
RESP-002 low-pressure focus
  -> VOICE-044 baseline delivery polish
  -> optional VOICE-041 private-pattern profile
  -> RESP-003 TTS selection
```

## Boundary

- Dry-run by default.
- No provider calls.
- No API key required.
- No raw private audio read.
- No private or customer audio upload.
- No transcription.
- No voice cloning.
- No provider voice identity change.
- No provider `style` or speed change.
- No protected campaign, compliance, handoff, hangup, or do-not-call text change.

## Commands

Run:

```powershell
python scripts\run_voice_044_baseline_delivery_polish.py
```

Validate:

```powershell
python scripts\validate_voice_044_baseline_delivery_polish.py
```
