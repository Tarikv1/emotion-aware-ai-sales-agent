# VOICE-008 Local TTS Smoke Test

## Experiment Goal

Test whether the project can generate local no-key TTS audio for approved agent responses before integrating a cloud voice provider.

The experiment covers:

- one German campaign response
- one English campaign response
- Windows SAPI local TTS attempt
- dry-run fallback when local TTS is unavailable

## Input

- Runner: `scripts/run_voice_008_local_tts_smoke.py`
- Validator: `scripts/validate_voice_008_local_tts_smoke.py`
- Case source: `research/experiments/cases/prod-005-realtime-latency-call-control.json`
- Provider attempted: `windows-sapi`
- Fallback provider: `dry-run`

## Current Result

Generated summary:

- cases: `2`
- German cases: `1`
- English cases: `1`
- audio files created: `0`
- dry-run fallback count: `2`
- response-language matches: `2 / 2`
- TTS text matches decision: `2 / 2`

Windows SAPI was available as a command path, but the environment did not have a usable local voice installed or allowed by the current security setting.

## Generated Artifacts

```text
research/experiments/generated/VOICE-008/VOICE-008-local-tts-smoke.json
research/experiments/generated/VOICE-008/VOICE-008-local-tts-smoke-report.md
```

Generated WAV files are not committed because they depend on local machine voice availability.

## Interpretation

VOICE-008 did not produce audible files in the current workspace, but it still produced a useful result:

- the local TTS path is integrated behind the existing voice packet contract
- the fallback path is explicit and validated
- no cloud provider was used
- no API key was required
- no customer audio was uploaded
- German and English response-language checks remained intact

This means local OS TTS should not be treated as a reliable production voice path. The next checkpoint should compare concrete TTS providers or local voice engines with known German and English support.

## Limitation

This experiment does not measure real TTS naturalness or production voice quality because no local voice was available in the current environment.

## Next Step

VOICE-009 should research concrete TTS provider options before selecting one integration candidate.
