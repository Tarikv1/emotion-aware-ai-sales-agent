# VOICE-043 Baseline Shaped Runtime Acceptance

VOICE-043 records the outcome of the VOICE-042 listening check: baseline shaped runtime sounded better than the private-pattern profile.

It is a dry-run acceptance checkpoint for the current preferred voice path.

## Decision

- Keep RESP-002 baseline shaped runtime as the preferred path.
- Do not promote VOICE-041 private-pattern settings as a runtime improvement.
- Keep VOICE-041 available only as an explicit experimental A/B harness.
- Future private-pattern variants must beat baseline in a listening review before promotion.

## What This Locks

The default runtime must keep:

- `voice_private_pattern_profile.enabled`: `false`
- `voice_private_pattern_profile.applied`: `false`
- `blocked_reason`: `profile_disabled`
- ElevenLabs `style`: `0.0`
- protected text unchanged
- no private-pattern provider settings unless a campaign/test explicitly enables them

## Boundary

- Dry-run only.
- No provider calls.
- No API key required.
- No raw private audio read.
- No private or customer audio upload.
- No transcription.
- No voice cloning.
- No generated audio.
- No quality claim beyond the narrow listening result: baseline beat VOICE-041 in this A/B.

## Commands

Run:

```powershell
python scripts\run_voice_043_baseline_shaped_runtime_acceptance.py
```

Validate:

```powershell
python scripts\validate_voice_043_baseline_shaped_runtime_acceptance.py
```
