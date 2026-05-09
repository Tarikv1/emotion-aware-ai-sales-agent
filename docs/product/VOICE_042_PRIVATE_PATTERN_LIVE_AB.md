# VOICE-042 Private Pattern Live A/B

VOICE-042 compares the accepted VOICE-041 abstract private speech-pattern profile against the normal RESP-002 shaped runtime voice path.

It is a live-capable listening checkpoint, not a runtime default.

## Purpose

- Compare baseline shaped runtime with VOICE-041 profile-enabled shaped runtime.
- Keep the same provider-facing TTS text across both variants.
- Isolate the effect of bounded provider settings, especially ElevenLabs `style` and `stability`.
- Require human listening review before any quality claim.

## Variants

- `baseline_shaped_runtime`: normal RESP-002 shaped runtime with VOICE-041 disabled.
- `private_pattern_profile`: same RESP-002 text with accepted VOICE-041 abstract private-pattern settings enabled.

The profile variant may adjust provider voice settings. It must not rewrite `final_response` or provider-facing TTS text.

## Current Listening Decision

Tarik's first listening review found the private-pattern direction useful, but the stronger profile was too loud and made roboticness more obvious.

VOICE-041 was revised to a subtler profile:

- target `style`: `0.06`
- maximum `style`: `0.08`
- stability delta: `-0.01`

After the softer repeat, baseline shaped runtime was preferred.

Decision: do not promote VOICE-041 as a runtime improvement. Keep baseline shaped runtime as the preferred path and keep VOICE-041 only as an experimental A/B harness.

## Boundary

- Default mode is dry-run.
- Live mode requires `--live` and `--limit-cases`.
- Provider keys and voice IDs stay environment-only or ignored local config.
- No raw private audio is read at runtime.
- No transcription.
- No private audio upload.
- No customer audio upload.
- No voice cloning.
- No audio quality claim before human listening review.

## Commands

Dry-run:

```powershell
python scripts\run_voice_042_private_pattern_live_ab.py
```

Live ElevenLabs run:

```powershell
python scripts\run_voice_042_private_pattern_live_ab.py --provider elevenlabs --live --limit-cases 1 --timeout-seconds 8
```

Validate:

```powershell
python scripts\validate_voice_042_private_pattern_live_ab.py
```
